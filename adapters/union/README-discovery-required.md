# Union Bank of India adapter — discovery required

No adapter is implemented here. Per the build specification's mandatory
constraint #8 ("No invented bank APIs"), this package stays empty until:

1. Union Bank supplies a documented, approved integration interface and
   test data (spec §6, "Bank-specific discovery deliverable").
2. Phase 0 discovery (spec §17) is completed for at least one real CC
   account walkthrough.

Until then, all Union-specific behaviour in the prototype uses the
`adapters/mock` equivalent (synthetic fixtures only).
