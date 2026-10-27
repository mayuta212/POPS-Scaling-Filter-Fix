/*
 * POPS Scaling Filter Fix v1.0.0 — PSP-3000 (04g), FW 6.61, POPS AV output.
 * Stock geometry; 256/320/640 -> Nearest, 368/512 -> Linear.
 * Re-evaluated on known GE render-path calls, including mode changes.
 * Signature checks and per-game POPS module relocation are mandatory.
 * No runtime tracing, dumps, or filesystem I/O.
 * Requires a full POPS restart when swapping or disabling the plugin.
 */
#include <pspkernel.h>
#include <pspmodulemgr.h>
#include <psputils.h>
#include <stdint.h>

PSP_MODULE_INFO("PopsScaleFilter", 0x1000, 1, 0);
#define POPS_REFERENCE_BASE 0x08B83C00u
#define POPS_SIZE  0x000FFE54u
#define FILTER_TEMPLATE 0x08C59EACu
#define HOOK 0x08B95BA4u
#define HOOK_REPLACE 0x0A2E2EC5u

typedef struct {uint32_t address,expected,value;} Patch;
typedef struct {uint32_t address,expected;} Guard;

static const Patch patches[] = {
    {0x08B855E0u,0x00000000u,0x3C0AC600u},
    {0x08B855E4u,0x00000000u,0x10000004u},
    {0x08B855E8u,0x00000000u,0x3C0E441Cu},
    {0x08B855ECu,0x00000000u,0x3C0AC600u},
    {0x08B855F0u,0x00000000u,0x354A0101u},
    {0x08B855F4u,0x00000000u,0x3C0E441Cu},
    {0x08B855F8u,0x00000000u,0x0A2E56EBu},
    {0x08B855FCu,0x00000000u,0xADCA9234u},
    {0x08B8BB14u,0x00000000u,0x00193840u},
    {0x08B8BB18u,0x00000000u,0x938E3663u},
    {0x08B8BB1Cu,0x00000000u,0x25CEFFFBu},
    {0x08B8BB20u,0x00000000u,0x15C02822u},
    {0x08B8BB24u,0x00000000u,0x332E0008u},
    {0x08B8BB28u,0x00000000u,0x11C0E6ADu},
    {0x08B8BB2Cu,0x00000000u,0x00000000u},
    {0x08B8BB30u,0x00000000u,0x0A2E157Bu},
    {0x08B8BB34u,0x00000000u,0x00000000u},
    {0x08B8BB38u,0x00000000u,0x00000000u},
    {0x08B8BB3Cu,0x00000000u,0x00000000u},
    {0x08B95BA4u,0x00193840u,0x0A2E2EC5u},
    {0x08C59EACu,0xC6000101u,0xC6000000u}
};
static const Guard guards[] = {
    {0x08B855DCu,0xA0880293u},
    {0x08B85600u,0x3C1D0980u},
    {0x08B8BB0Cu,0x03E00008u},
    {0x08B8BB10u,0x27BD0010u},
    {0x08B8BB24u,0x00000000u},
    {0x08B8BB30u,0x00000000u},
    {0x08B8BB38u,0x00000000u},
    {0x08B8BB3Cu,0x00000000u},
    {0x08B8BB40u,0x27BDFFE0u},
    {0x08B95B98u,0x93590000u},
    {0x08B95BA0u,0x01CD0018u},
    {0x08B95BA8u,0x0000C012u},
    {0x08B95BACu,0x27030080u},
    {0x08B95BB4u,0x934A0007u},
    {0x08B9FD78u,0x3C0908C6u},
    {0x08B9FD80u,0x25259E78u},
    {0x08B9FD84u,0x35049200u},
    {0x08B9FD88u,0x0E2F0751u},
    {0x08B9FD8Cu,0x24060064u},
    {0x08C59EA8u,0xB8000909u},
    {0x08C59EB0u,0xC9000104u},
    {0x08C59EF0u,0xC6000000u},
    {0x08C59F38u,0xC6000000u}
};
/*
 * Runtime rebasing. The signature tables use addresses from the user's
 * offline POPS dump; no absolute-POPS-address assumptions at runtime.
 * Rebase J/JAL targets when targets are internal to this very module.
 * Branch offsets stay fixed, as MIPS conditional branches are PC-relative.
 * A single verified LUI/ADDIU address-forming pair also needs rebasing.
 * A mismatch is diagnostic only, NEVER guessed into a write.
 */
static uint32_t active_base=POPS_REFERENCE_BASE;
static uint32_t rebase_addr(uint32_t old){
    return active_base + (old - POPS_REFERENCE_BASE);
}
static int internal_target(uint32_t target){
    return (target >= POPS_REFERENCE_BASE && target-POPS_REFERENCE_BASE<POPS_SIZE);
}
static uint32_t rebase_insn(uint32_t pc, uint32_t insn){
    uint32_t op=insn>>26;
    if(op==2u || op==3u){ /* J / JAL to internal text */
        uint32_t old_target=((pc+4u)&0xF0000000u)|((insn&0x03FFFFFFu)<<2);
        if(internal_target(old_target)){
            uint32_t target=rebase_addr(old_target);
            if((target & 0xF0000000u)!=((rebase_addr(pc)+4u)&0xF0000000u))
                return 0u; /* pointer crosses a MIPS J segment */
            return (insn&0xFC000000u)|((target>>2)&0x03FFFFFFu);
        }
    }
    /* POPS original address of GE command template: lui t1,hi; addiu a1,t1,lo. */
    if(pc==0x08B9FD78u && insn==0x3C0908C6u){
        uint32_t target=rebase_addr(0x08C59E78u);
        return 0x3C090000u|(((target+0x8000u)>>16)&0xFFFFu);
    }
    if(pc==0x08B9FD80u && insn==0x25259E78u){
        uint32_t target=rebase_addr(0x08C59E78u);
        return 0x25250000u|(target&0xFFFFu);
    }
    return insn;
}
#define NP ((int)(sizeof(patches)/sizeof(patches[0])))
#define NG ((int)(sizeof(guards)/sizeof(guards[0])))

static int equals(const char *a,const char *b){
    while (*a && *b) {if (*a!=*b) return 0;a++;b++;}
    return (*a==*b);
}
static int find_pops(SceKernelModuleInfo *result){
    SceUID ids[128];int count=0,i;
    if(sceKernelGetModuleIdList(ids,sizeof(ids),&count)<0) return 0;
    if(count>128) count=128;
    for(i=0;i<count;i++){
        SceKernelModuleInfo m;m.size=sizeof(m);
        if(sceKernelQueryModuleInfo(ids[i],&m)>=0 && equals(m.name,"pops")){
            *result=m;return 1;
        }
    }
    return 0;
}
static int verify_signatures(void){
    int i, nbad=0;
    uint32_t a,expected,got;
    for(i=0;i<NG;i++){
        a=rebase_addr(guards[i].address);
        expected=rebase_insn(guards[i].address,guards[i].expected);
        got=*(volatile uint32_t *)(uintptr_t)a;
        if((guards[i].expected!=0u && expected==0u) || got!=expected)
            ++nbad;
    }
    for(i=0;i<NP;i++){
        a=rebase_addr(patches[i].address);
        expected=rebase_insn(patches[i].address,patches[i].expected);
        got=*(volatile uint32_t *)(uintptr_t)a;
        if((patches[i].expected!=0u && expected==0u) || got!=expected)
            ++nbad;
    }
    return nbad;
}
static int worker(SceSize size, void *arg){
    SceKernelModuleInfo m;
    int i, found=0, mismatch, oldintr;
    (void)size; (void)arg;
    /* POPS may load after the PRX. Poll only during startup. */
    for(i=0;i<90;i++){
        if(find_pops(&m)){found=1;break;}
        sceKernelDelayThread(200000);
    }
    if(!found || (uint32_t)m.text_size!=POPS_SIZE) return 0;
    active_base=(uint32_t)(uintptr_t)m.text_addr;
    if(active_base<0x08800000u || active_base>0x0A000000u || (active_base&3u)!=0u)
        return 0;
    /* Fail closed on unsupported/different POPS text. */
    if(verify_signatures()!=0) return 0;
    oldintr=sceKernelCpuSuspendIntr();
    mismatch=verify_signatures();
    if(!mismatch){
        /* Install all support code before making the entry hook reachable. */
        for(i=0;i<NP;i++) if(patches[i].address!=HOOK)
            *(volatile uint32_t *)(uintptr_t)rebase_addr(patches[i].address)=
                rebase_insn(patches[i].address,patches[i].value);
        sceKernelDcacheWritebackInvalidateAll();
        sceKernelIcacheInvalidateAll();
        *(volatile uint32_t *)(uintptr_t)rebase_addr(HOOK)=
            rebase_insn(HOOK,HOOK_REPLACE);
        sceKernelDcacheWritebackInvalidateAll();
        sceKernelIcacheInvalidateAll();
    }
    sceKernelCpuResumeIntr(oldintr);
    return 0;
}
int module_start(SceSize args,void *argp){
    SceUID th;
    (void)args;(void)argp;
    th=sceKernelCreateThread("PopsScaleFilter",worker,0x18,0x2000,0,0);
    if(th>=0) sceKernelStartThread(th,0,0);
    return 0;
}
int module_stop(SceSize args,void *argp){
    (void)args;(void)argp;
    return 0;
}
