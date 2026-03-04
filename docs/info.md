<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## Description

This project implements a small synchronous glitch art generator. It produces an 8-bit output value each clock cycle. The pattern is determined based on a seed input and a mode select input.

## How it works

The design uses three main components:
 * 8-bit LFSR - generates a deterministic pseudo-random sequence based on the input seed.
 * 8-bit counter - increments every update cycle to introduce motion into the pattern.
 * Mode selector (2 bits) - selects on of four mixing functions that combine the LFSR and counter using simple bitwise operations

Each mode uses different feedback taps and mixing logic, producing visually distinct patterns.

## Testbench and why it's sufficient

The design is tested using a cocoTB testbench that simulates the ckt and verifies its outputs using assertions. A small reference model of the LFSR, counter, and pixel generation logic is implemented in python to compute the expected output values.

The test covers:
 * reset behavior and the seed = 0 corner case
 * all 4 modes
 * multiple seed values (00,01, A5, FF)
 * multi-cycle checking to verify correct sequential behavior
 * ena hold behavior (output/state cannot change when ena = 0)
 
## GenAI usage
I used chatGPT to help brainstorm project ideas and to review the verilog and cocotb testbench implementation.
