TARGET = PopsScaleFilter
OBJS = main.o
BUILD_PRX = 1
PSP_FW_VERSION = 661
USE_KERNEL_LIBS = 1
PRX_EXPORTS = exports.exp
CFLAGS = -O2 -G0 -Wall -Wextra -fno-pic -fno-builtin
LIBS = -lpspkernel
PSPSDK = $(shell psp-config --pspsdk-path)
include $(PSPSDK)/lib/build.mak
