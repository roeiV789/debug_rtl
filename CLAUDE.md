# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an RTL (Register Transfer Level) debugging workspace for an **AXI-Lite Write Channel Controller**. The goal is protocol compliance verification and FSM behavior analysis by comparing a behavioral specification against simulation trace data.

## Key Files

- **`write_channel_controller_spec.yml`** — Protocol rules and FSM definition for the memory controller write channel. The authoritative source for expected behavior.
- **`write_channel_controller_sim.csv`** — Simulation waveform trace (24 cycles) capturing actual signal behavior for comparison against the spec.

## Specification Structure

**Protocol Rules** defined in the spec:
- `ERR_RULE_01`: AWREADY must respond within 5 cycles of AWVALID asserting (timeout = bus starvation risk).
- `ERR_RULE_02`: BVALID must not assert before both AW and W handshakes complete.

**FSM (`MEM_CTRL_FSM`) valid transitions:**
```
IDLE → SETUP → BUSY → RESP_WAIT → IDLE
```
Each state also allows a self-loop. SETUP can return to IDLE on reset.

## Simulation Trace Signals

| Signal | Description |
|---|---|
| `cycle` / `clk` / `rst_n` | Timing and reset (rst_n active-low, deasserts at cycle 2) |
| `awvalid` / `awready` | Write address handshake |
| `wvalid` / `wready` | Write data handshake |
| `bvalid` / `bready` | Write response handshake |
| `fifo_full` | Blocks AWREADY when asserted |
| `fsm_state` | Current FSM state string |

## Debugging Workflow

The typical analysis task is: identify cycles where the simulation trace violates protocol rules or produces invalid FSM transitions defined in the spec. Look for:
1. AWVALID asserted but AWREADY delayed beyond 5 cycles (rule ERR_RULE_01).
2. BVALID asserting before AW+W handshakes both complete (rule ERR_RULE_02).
3. FSM state transitions not in the allowed set from the spec.
4. `fifo_full` interactions that may mask or cause rule violations.
