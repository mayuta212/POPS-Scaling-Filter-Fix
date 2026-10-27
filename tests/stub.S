/* v1.0.0 — per-render AV adaptive GE TEXFILTER, stock X and Y.
 * This is verification source ONLY: main.c embeds these exact opcodes;
 * do NOT link this stub into the PRX.
 * Hook at 0x08B95BA4: J mode_router; original delay-slot mflo t8 intact.
 * t9 descriptor: 80(256), 64(320), 56(368), 40(512), 32(640).
 * 256/320/640 => C6000000. 368/512 => C6000101. Known descriptors only.
 * Non-AV => no runtime TEXFILTER write.
 */
.set noreorder
.set noat
.text
.org 0
nearest:
    lui $10,0xc600
    beq $0,$0,store_filter
    lui $14,0x441c
linear:
    lui $10,0xc600
    ori $10,$10,0x0101
    lui $14,0x441c
store_filter:
    .word 0x0A2E56EB /* j POPS return, never let assembler relax to b */
    sw $10,-0x6dcc($14)
.org 0x6534
mode_router:
    sll $7,$25,1
    lbu $14,0x3663($28)
    addiu $14,$14,-5
    .word 0x15C02822 /* bne t6,zero,0x08B95BAC, PC-relative signed immediate */
    andi $14,$25,0x0008 /* 80/64/32 have bit3=0; 56/40 have bit3=1 */
    beq $14,$0,nearest
    nop
    .word 0x0A2E157B /* j linear; preserve absolute J for rebasing */
    nop
    nop
    nop
