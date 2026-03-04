/*
 * Copyright (c) 2026 Angelica Arroyo
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_aaroy13_glitchgen (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // All output pins must be assigned. If not used, assign to 0
  assign uio_out = 8'b0;
  assign uio_oe  = 8'b0;

  // input mapping
  wire [7:0] seed = ui_in;
  wire [1:0] mode  = uio_in[1:0];

  // internal state registers
  logic [7:0] lfsr; //pseudo-random generator
  logic [7:0] ctr; //simple counter for struct
  logic [7:0] out_q;  //registered output

  // output is registered
  assign uo_out = out_q;

  //rotate helpers
  wire [7:0] rot1 = {lfsr[6:0], lfsr[7]}; //rotate left by 1
  wire [7:0] rot3 = {lfsr[4:0], lfsr[7:5]}; //rotate left by 3
    wire [7:0] ctr_swiz = {ctr[3:0], ctr[7:4]};  //swap upper/lower nibbles

  //lfsr feedback depends on selected mode
  logic fb;
  always_comb begin
      case (mode)
          2'b00: fb = lfsr[7] ^ lfsr[5] ^ lfsr[4] ^ lfsr[3];
          2'b01: fb = lfsr[7] ^ lfsr[6] ^ lfsr[5] ^ lfsr[1];
          2'b10: fb = lfsr[7] ^ lfsr[2] ^ lfsr[1] ^ lfsr[0];
          2'b11: fb = lfsr[7] ^ lfsr[4] ^ lfsr[2] ^ lfsr[1];
          default: fb = lfsr[7] ^ lfsr[5] ^ lfsr[4] ^ lfsr[3];
      endcase
  end

  wire [7:0] lfsr_next = {lfsr[6:0], fb};  //next lfsr state
    
  // pixels generation logic
  logic [7:0] pixel;
  always_comb begin
      case (mode)
          2'b00: pixel = lfsr;  //noise pattern
          2'b01: pixel = lfsr ^ ctr;    //streaks pattern
          2'b10: pixel = lfsr ^ ctr_swiz ^ rot3;   //blocky glitch
          2'b11: pixel = (lfsr ^ rot3) ^ (ctr | rot1);   //structured texture
          default: pixel = lfsr;
      endcase
  end

  //sequential logic
  always_ff @(posedge clk) begin
      if (!rst_n) begin
          lfsr <= (seed == 8'h00) ? 8'h01 : seed;
          ctr <= 8'h00;
          out_q <= 8'h00;
      end else if (ena) begin
          lfsr <= lfsr_next;
          ctr <= ctr + 8'd1;
          out_q <= pixel;
      end
  end 

endmodule

`default_nettype wire

