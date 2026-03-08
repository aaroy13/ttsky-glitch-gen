# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

#help functions

#rotate an 8-bit val left
def rotl8(x, r):
    x &= 0xFF
    return ((x << r) | (x >> (8 - r))) & 0xFF

#swap upper and lower nibbles
def swiz(x):
    x &= 0xFF
    return ((x & 0x0F) << 4) | ((x & 0xF0) >> 4)

#compute the feedback bit for the lfsr depnding on mode
def fb_bit(l, mode):
    b = [(l >> i) & 1 for i in range(8)]
    if mode == 0:
        return b[7] ^ b[5] ^ b[4] ^ b[3]
    if mode == 1:
        return b[7] ^ b[6] ^ b[5] ^ b[1]
    if mode == 2:
        return b[7] ^ b[2] ^ b[1] ^ b[0]
    return b[7] ^ b[4] ^ b[2] ^ b[1]

# compute the next lfsr val
def lfsr_next(l, mode):
    fb = fb_bit(l, mode) & 1
    return (((l << 1) & 0xFE) | fb) & 0xFF
    
# compute the expected pixel output for a given state
def pixel(l, c, mode):
    rot1 = rotl8(l, 1)
    rot3 = rotl8(l, 3)
    cs = swiz(c)
    if mode == 0:
        return l  # noise pattern
    if mode == 1:
        return l ^ c  # streak pattern
    if mode == 2:
        return l ^ cs ^ rot3   # blocky glitch
    return (l ^ rot3) ^ (c | rot1)  # structured texture

#--DUT control helpers--

#apply rst and initialize reference model
async def reset_dut(dut, seed, mode):
    dut.ui_in.value = seed & 0xFF
    dut.uio_in.value = mode & 0x3
    dut.ena.value = 1
    dut.rst_n.value = 0

    #hold rst low for 2 clk edges
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    
    await Timer(1, unit="ns")
    
    # Reference state
    ref_l = 0x01 if (seed & 0xFF) == 0 else (seed & 0xFF)
    ref_c = 0
    
    return ref_l, ref_c

#step simulation by one clock and check output
async def step_check(dut, ref_l, ref_c, mode):
    exp = pixel(ref_l, ref_c, mode)
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")   # allow signals to settle

    assert dut.uo_out.value.is_resolvable, f"Fail: uo_out has unknwn bits {dut.uo_out.value}"
    got = dut.uo_out.value.integer & 0xFF

    # Self-checking assertion
    assert got == exp, (
        f"FAIL mode={mode} seed={int(dut.ui_in.value):02x} "
        f"ref_lfsr={ref_l:02x} ref_ctr={ref_c:02x} "
        f"got={got:02x} exp={exp:02x}"
    )
    # Advance reference model
    if int(dut.ena.value) == 1:
        ref_l = lfsr_next(ref_l, mode)
        ref_c = (ref_c + 1) & 0xFF
    return ref_l, ref_c

# main test
@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 1
    
    await Timer(20, unit="ns")

    # Keep testing the module by changing the input values, waiting for
    # one or more clock cycles, and asserting the expected output values.

    #test 1: test for several seeds and all 4 modes
    seeds = [0x00, 0x01, 0xA5, 0xFF]

    for mode in range(4):
        for seed in seeds:
            ref_l, ref_c = await reset_dut(dut, seed, mode)
            # Check several cycles of operation
            for _ in range(8):
                ref_l, ref_c = await step_check(dut, ref_l, ref_c, mode)
                
    #test 2:verify enable signal holds output
    mode = 1
    ref_l, ref_c = await reset_dut(dut, 0x3C, mode)
    ref_l, ref_c = await step_check(dut, ref_l, ref_c, mode)

    assert dut.uo_out.value.is_resolvable, f"Fail: uo_out has unknwn bits {dut.uo_out.value}"
    held = dut.uo_out.value.integer & 0xFF
    dut.ena.value = 0

    # Output should remain constant while ena=0
    for _ in range(5):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert dut.uo_out.value.is_resolvable, "Fail: uo_out has unknwn bits {dut.uo_out.value}"
        assert ((dut.uo_out.value.integer & 0xFF) == held), "FAIL: ena hold violated"

    # Re-enable and continue checking
    dut.ena.value = 1

    for _ in range(4):
        ref_l, ref_c = await step_check(dut, ref_l, ref_c, mode)

    dut._log.info("PASS")
    
