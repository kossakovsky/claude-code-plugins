Ask the user ONE question at a time. Do NOT ask about output directories, task IDs, or scan names.

Handle each access method completely before moving to the next.

1. If Kubernetes is selected:
   "Which context? Run `kubectl config get-contexts` and paste the name."
   After getting the context, ask: "Which node should I SSH into to run kubectl?"

2. If SSH is selected (after or separate from K8s):
   "Which compute instances should I scan directly over SSH?
   These are VMs that are NOT managed by Kubernetes.
   List ALL IPs or hostnames, or say 'none' if everything is in K8s."

3. If cloud APIs / Teleport / Ansible are selected:
   - cloud APIs → "Which provider? What account/project? Which region?"
   - Teleport → "Which cluster? What user?"
   - Ansible → "Which inventory file or host group?"

4. For each SSH target, ask: "Which SSH key? Which user?"
   The answer must be CONCRETE. "default" is acceptable for the key path.

5. If the user cannot provide specific targets, set `discovery_mode: true`.

Write `{run_dir}/connection_config.json` per schemas/connection-config.schema.json.
This step is NOT complete until the file passes schema validation.
