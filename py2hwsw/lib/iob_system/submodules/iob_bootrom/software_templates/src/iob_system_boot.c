/*
 * SPDX-FileCopyrightText: 2025 IObundle
 *
 * SPDX-License-Identifier: MIT
 */

#include "iob_bsp.h"
#include "iob_system_conf.h"
#include "iob_system_mmap.h"
#include "iob_uart.h"

#define PROGNAME "IOb-Bootloader"

int main() {

  // init uart
  uart_init(UART0_BASE, IOB_BSP_FREQ / IOB_BSP_BAUD);

  // connect with console
  do {
    if (iob_uart_get_txready())
      uart_putc((char)ENQ);
  } while (!iob_uart_get_rxready());

  // welcome message
  uart_puts(PROGNAME);
  uart_puts(": connected!\n");

#ifdef IOB_SYSTEM_USE_EXTMEM
  uart_puts(PROGNAME);
  uart_puts(": DDR in use.\n");
#endif

  // address to copy firmware to
  char *prog_start_addr = (char *)IOB_SYSTEM_FW_BASEADDR;

  while (uart_getc() != ACK) {
    uart_puts(PROGNAME);
    uart_puts(": Waiting for Console ACK.\n");
  }

#ifndef IOB_SYSTEM_INIT_MEM
  // receive firmware from host
  int file_size = 0;
  char r_fw[] = "iob_system_firmware.bin";
  file_size = uart_recvfile(r_fw, prog_start_addr);
  uart_puts(PROGNAME);
  uart_puts(": Loading firmware...\n");

  // sending firmware back for debug
  char s_fw[] = "s_fw.bin";

  if (file_size)
    uart_sendfile(s_fw, file_size, prog_start_addr);
  else {
    uart_puts(PROGNAME);
    uart_puts(": ERROR loading firmware\n");
  }
#endif

  // run firmware
  uart_puts(PROGNAME);
  uart_puts(": Restart CPU to run user program...\n");
  uart_txwait();
}
