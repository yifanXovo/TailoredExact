# Uniform Windows measurement affinity

Microsoft documents SetProcessAffinityMask as a process-thread mask inherited
by child processes. GetProcessAffinityMask returns process/system masks;
check API return values and readback rather than assuming success. This
workstation has one group and20 logical processors. Only an owned launcher
is set, before a child starts, and every full arm uses the same mask. No other
process/service/priority is modified. No algorithm decision reads the mask,
a CPU rate or a remaining-resource ratio.

Official API sources checked during preflight:

- https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setprocessaffinitymask
- https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getprocessaffinitymask

Fixed logical2/mask4 uses the read-only topology saved in Round69 (efficiency
class1). It does not reserve a core or eliminate every source of system
variation. Fresh controls are required; old default-affinity measurements
remain historical and are not strict new timing pairs.
