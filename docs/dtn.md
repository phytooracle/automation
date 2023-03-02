
1. Log on to the HPC:

```bash
ssh <your NetID here>@hpc.arizona.edu
```

2. Once on the head node, access puma:

```bash
puma
```

3. Create an SSH key:

```bash
ssh-keygen -t rsa
```

4. Copy the SSH key to the Bastion Host:

```bash
ssh-copy-id <your NetID here>@hpc.arizona.edu
```

>NOTE: Enter your password and follow the two-factor authentication.

5. Copy the SSH key to the DTN:

```bash
ssh-copy-id <your NetID here>@filexfer.hpc.arizona.edu
```

>NOTE: Enter your password and follow the two-factor authentication.

6. Confirm that the SSH key works by accessing the DTN without being prompted for a password:

```bash
ssh filexfer
```
> NOTE: If you are still prompted for a password, submit a UA HPC support ticket [here](https://uarizona.service-now.com/sp?id=sc_cat_item&sys_id=8c4aa2761b1df0107947edf1604bcbd0&sysparm_category=84d3d1acdbc8f4109627d90d6896191f).