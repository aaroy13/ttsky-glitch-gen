<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

This project implements a small synchronous glitch art generator.
The design uses three main components:
 * 8-bit LFSR - generates a deterministic pseudo-random sequence based on the input seed.
 * 8-bit counter - increments every update cycle to introduce motion into the pattern.
 * Mode selector (2 bits) - selects on of four mixing functions that combine the LFSR and counter using simple bitwise operations

## How to test

Use make to run the included  simulation testbench. This will compile the design and execute the test located in test/tb.v.

