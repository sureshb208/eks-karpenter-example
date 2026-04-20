# Production EKS 1.33 Architecture Guide: Spark + Karpenter

## 1. Recommended Architecture and Module Boundaries

### Module Structure

```
┌─────────────────────────────────────────────────────────────┐
│ Foundation Layer (Base/Network)                             │
├─────────────────────────────────────────────────────────────┤
│ - VPC Module                                                │
│   • Public/Private subnets (3+ AZs)                        │
│   • NAT Gateways (HA: one per AZ)                          │
│   • VPC endpoints (S3, ECR, EKS API, etc.)                 │
│   • Route53 private hosted zones                            │
│   • Security groups (base rules only)                      │
│   • Outputs: vpc_id, subnet_ids, security_group_ids        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ EKS Control Plane Module                                    │
├─────────────────────────────────────────────────────────────┤
│ - EKS Cluster                                               │
│   • Cluster version 1.33                                    │
│   • Control plane logging (all types)                       │
│   • IRSA enabled (OIDC provider)                           │
│   • Encryption at rest (KMS)                                │
│   • Public endpoint (restricted CIDRs)                     │
│   • Private endpoint enabled                                │
│   • Addon: VPC CNI (custom networking)                     │
│   • Addon: CoreDNS                                          │
│   • Addon: kube-proxy                                       │
│   • Security group tagging for Karpenter discovery         │
│   • Outputs: cluster_name, oidc_provider_arn, endpoint     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Karpenter Module                                            │
├─────────────────────────────────────────────────────────────┤
│ - Karpenter Installation                                    │
│   • Helm chart (v1.3.1+)                                    │
│   • IRSA role with Karpenter permissions                   │
│   • SQS queue for Spot interruption handling               │
│   • EC2NodeClass resources (via kubectl_manifest)         │
│   • NodePool resources (via kubectl_manifest)              │
│   • Node IAM instance profile                               │
│   • Outputs: karpenter_irsa_arn, queue_name                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Node Groups Module (System Workloads)                       │
├─────────────────────────────────────────────────────────────┤
│ - Managed Node Groups                                       │
│   • System node group (CoreDNS, metrics, etc.)             │
│   • Small instance (t3.medium or t4g.medium)               │
│   • Multi-AZ placement                                      │
│   • Taints: CriticalAddonsOnly=true:NoSchedule             │
│   • Labels: workload-type=system                            │
│   • NOT for Spark workloads                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Addons Module                                               │
├─────────────────────────────────────────────────────────────┤
│ - Cluster Addons                                            │
│   • AWS Load Balancer Controller (ALB/NLB)                 │
│   • Cluster Autoscaler (disabled - Karpenter handles it)  │
│   • Metrics Server                                          │
│   • Cluster Autoscaler (if needed for system nodes)        │
│   • External Secrets Operator                               │
│   • Cert Manager (if using TLS)                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Networking Module                                           │
├─────────────────────────────────────────────────────────────┤
│ - Load Balancers                                            │
│   • ALB Ingress Controller                                  │
│   • NLB for L4 traffic (Spark shuffle, etc.)               │
│   • Target groups and listeners                            │
│ - Route53                                                   │
│   • Private hosted zone records                             │
│   • Service discovery entries                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Application Deployment Module                               │
├─────────────────────────────────────────────────────────────┤
│ - Spark Operator (optional)                                 │
│ - Spark Application manifests                               │
│ - Service accounts with IRSA                               │
│ - ConfigMaps for Spark configs                             │
└─────────────────────────────────────────────────────────────┘
```

### Module Dependencies

```
VPC → EKS → Karpenter → Addons → Networking → Apps
  ↓      ↓       ↓
Nodes (system)  (Spark nodes via Karpenter)
```

### Module Boundaries - What Goes Where

**VPC Module:**
- Network infrastructure only
- No EKS-specific resources
- Outputs: subnet IDs, security group IDs, VPC ID

**EKS Module:**
- Cluster creation and configuration
- Control plane security groups
- IRSA setup
- Base addons (CNI, CoreDNS, kube-proxy)
- NO node groups (except system)

**Karpenter Module:**
- Karpenter installation (Helm)
- Karpenter IAM roles (IRSA + node role)
- EC2NodeClass definitions
- NodePool definitions
- SQS queue for interruptions
- Depends on: EKS module

**Node Groups Module:**
- Only system/managed node groups
- Small, stable nodes for system pods
- Taints to prevent Spark scheduling
- Depends on: EKS module

**Addons Module:**
- Optional cluster addons
- Load balancer controllers
- Monitoring agents
- Depends on: EKS module

**Networking Module:**
- ALB/NLB resources
- Route53 records
- Service discovery
- Depends on: EKS, Addons modules

**App Deployment Module:**
- Spark job definitions
- Application manifests
- Service accounts
- Depends on: All above modules

### Terraform Workspace Strategy

```
Workspace: foundation
  - VPC module
  - Remote state: terraform-state-<account>-<region>/foundation

Workspace: eks-control-plane
  - EKS module
  - Remote state: terraform-state-<account>-<region>/eks-control-plane
  - Data source: VPC outputs from foundation workspace

Workspace: karpenter
  - Karpenter module
  - Remote state: terraform-state-<account>-<region>/karpenter
  - Data source: EKS outputs from eks-control-plane workspace

Workspace: system-nodes
  - Node groups module
  - Remote state: terraform-state-<account>-<region>/system-nodes
  - Data source: EKS outputs from eks-control-plane workspace

Workspace: addons
  - Addons module
  - Remote state: terraform-state-<account>-<region>/addons
  - Data source: EKS outputs from eks-control-plane workspace

Workspace: networking
  - Networking module
  - Remote state: terraform-state-<account>-<region>/networking
  - Data source: EKS, Addons outputs

Workspace: apps
  - App deployment module
  - Remote state: terraform-state-<account>-<region>/apps
  - Data source: All above modules
```

---

## 2. Network Design and Traffic Flow

### Network Topology

```
Internet
   │
   ├─→ ALB (Public) ──→ Ingress ──→ Spark UI Services
   │
   └─→ NLB (Public/Private) ──→ Spark Shuffle Services (L4)
        │
        └─→ Pod-to-Pod Communication (East-West)

VPC (10.0.0.0/16)
├─ Public Subnets (10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24)
│  ├─ NAT Gateways (one per AZ)
│  └─ Internet Gateway
│
└─ Private Subnets (10.0.10.0/22, 10.0.20.0/22, 10.0.30.0/22)
   ├─ EKS Control Plane Endpoints
   ├─ EKS Nodes (Karpenter-provisioned)
   ├─ Spark Driver Pods
   ├─ Spark Executor Pods
   └─ System Pods (CoreDNS, metrics, etc.)

VPC Endpoints (PrivateLink)
├─ com.amazonaws.<region>.s3
├─ com.amazonaws.<region>.ecr.api
├─ com.amazonaws.<region>.ecr.dkr
├─ com.amazonaws.<region>.eks
└─ com.amazonaws.<region>.logs
```

### Traffic Flow Patterns

#### North-South Traffic (External → Cluster)

**Spark UI Access:**
```
Internet → ALB (L7) → Ingress Controller → Spark UI Service → Spark Driver Pod
```

**Spark Job Submission:**
```
Developer → kubectl → EKS API Endpoint (Private/Public) → Spark Operator/Job Controller
```

**Data Ingestion:**
```
S3 → VPC Endpoint → Spark Executor Pods (reading data)
```

#### East-West Traffic (Internal Cluster)

**Spark Shuffle (Critical for Performance):**
```
Spark Executor Pod (AZ-1) → NLB → Spark Executor Pod (AZ-2)
  OR
Spark Executor Pod (AZ-1) → Direct Pod-to-Pod (same subnet)
```

**Spark Driver ↔ Executor:**
```
Spark Driver Pod → Spark Executor Pods (direct pod IP)
```

**Service Discovery:**
```
Spark Executor → CoreDNS → Spark Driver Service
```

### Network Configuration Requirements

**VPC CNI Configuration:**
- Use custom networking mode for better IP utilization
- Configure `WARM_ENI_TARGET` and `WARM_IP_TARGET` for Spark burst scenarios
- Enable prefix delegation for large pods

**Security Group Rules:**

**Cluster Security Group:**
- Allow all traffic from node security group
- Allow control plane to nodes (1025-65535)

**Node Security Group:**
- Allow all traffic from cluster security group
- Allow all traffic from self (pod-to-pod)
- Allow ingress from ALB security group (if needed)
- Allow ingress from NLB security group (for shuffle)

**ALB Security Group:**
- Allow ingress from allowed CIDRs (corporate network)
- Allow egress to node security group

**NLB Security Group:**
- Allow ingress from node security group (for shuffle)
- Allow ingress from VPC CIDR (internal only)

### Subnet Tagging for Karpenter

All private subnets must have:
```
karpenter.sh/discovery: <cluster-name>
```

This allows Karpenter to automatically discover subnets for node provisioning.

---

## 3. Spark Autoscaling Interaction with Karpenter

### How Spark Dynamic Allocation Works with Karpenter

**Spark Dynamic Allocation Flow:**

1. **Job Submission:**
   ```
   Spark Driver Pod created → Pending (no suitable nodes)
   ```

2. **Karpenter Provisioning:**
   ```
   Karpenter sees pending pod → Evaluates resource requests
   → Selects instance type from NodePool
   → Provisions EC2 instance (30-60 seconds)
   → Node joins cluster → Pod scheduled
   ```

3. **Spark Executor Scaling:**
   ```
   Spark requests more executors → New executor pods created
   → Karpenter provisions additional nodes if needed
   → Executors start → Spark job scales up
   ```

4. **Spark Executor Scaling Down:**
   ```
   Spark releases executors → Pods terminated
   → Nodes become underutilized
   → Karpenter consolidation (after TTL)
   → Nodes drained and terminated
   ```

### Critical Configuration Points

**Spark Configuration:**
```
spark.dynamicAllocation.enabled=true
spark.dynamicAllocation.minExecutors=2
spark.dynamicAllocation.maxExecutors=100
spark.dynamicAllocation.initialExecutors=5
spark.dynamicAllocation.executorIdleTimeout=60s
spark.dynamicAllocation.schedulerBacklogTimeout=1s
spark.dynamicAllocation.sustainedSchedulerBacklogTimeout=5s
```

**Karpenter NodePool Configuration:**
- Match instance types to Spark executor sizes
- Set appropriate CPU/memory limits
- Configure TTL for consolidation (60-120s for Spark)
- Use Spot instances with interruption handling

**Pod Resource Requests:**
- MUST set accurate resource requests (CPU + memory)
- Karpenter uses requests to select instance type
- Too small = oversized instances (waste)
- Too large = unschedulable pods

### Node Pool Strategy for Spark

**Spark General Purpose Pool:**
- Instance types: m6i, m7i (large to 4xlarge)
- Use for: Most Spark ETL jobs
- Spot preference: Yes (with interruption handling)

**Spark Memory Pool:**
- Instance types: r6i, r7i, r8g (xlarge to 8xlarge)
- Use for: Large shuffle operations, caching
- Spot preference: Yes (with higher interruption risk tolerance)

**Spark Compute Pool:**
- Instance types: c6i, c7i (xlarge to 8xlarge)
- Use for: CPU-intensive transformations
- Spot preference: Yes

**On-Demand Pool (Production Critical):**
- Instance types: m6i, r6i (same as above)
- Use for: Critical production jobs
- Spot preference: No (use nodeSelector to prefer on-demand)

### Pod Scheduling Strategy

**Node Selectors:**
```yaml
nodeSelector:
  spark-workload: "true"
  workload-type: spark-general  # or spark-memory, spark-compute
```

**Affinity Rules:**
```yaml
affinity:
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
            - key: karpenter.sh/capacity-type
              operator: In
              values: ["spot"]
```

**Tolerations (if using taints):**
```yaml
tolerations:
- key: spark-workload
  operator: Equal
  value: "true"
  effect: NoSchedule
```

### Spark Shuffle Service Configuration

For large shuffle operations, configure Spark to use external shuffle service:

```
spark.shuffle.service.enabled=true
spark.dynamicAllocation.shuffleTracking.enabled=true
```

This allows executors to be removed while shuffle data is still available.

---

## 4. Failure Scenarios and Prevention

### Scenario 1: Karpenter Cannot Provision Nodes

**Symptoms:**
- Pods stuck in Pending state
- No new nodes appearing
- Karpenter logs show errors

**Root Causes:**
1. **IAM Permissions:**
   - Karpenter IRSA role missing EC2 permissions
   - Node instance profile missing EKS join permissions

2. **Subnet/Security Group Discovery:**
   - Missing `karpenter.sh/discovery` tags on subnets
   - Missing tags on security groups
   - Subnets in wrong AZs

3. **Instance Limits:**
   - EC2 instance limit reached
   - Spot instance capacity exhausted

4. **NodePool Limits:**
   - CPU or memory limits reached
   - No suitable instance types in pool

**Prevention:**
- Validate IAM roles before deployment
- Tag all resources correctly
- Monitor EC2 limits (use Service Quotas)
- Set appropriate NodePool limits
- Include multiple instance types in pools

**Validation Commands:**
```bash
# Check Karpenter IAM role
aws iam get-role-policy --role-name <karpenter-role> --policy-name <policy>

# Check subnet tags
aws ec2 describe-subnets --filters "Name=tag:karpenter.sh/discovery,Values=<cluster-name>"

# Check EC2 limits
aws service-quotas get-service-quota --service-code ec2 --quota-code L-34B43A08

# Check Karpenter logs
kubectl logs -n karpenter -l app.kubernetes.io/name=karpenter -c controller
```

### Scenario 2: Spark Jobs Fail Due to Spot Interruptions

**Symptoms:**
- Spark executors terminated unexpectedly
- Jobs fail with "ExecutorLost" errors
- Frequent job restarts

**Root Causes:**
1. Spot instance interruptions
2. No interruption handling in Spark
3. Jobs not configured for retry

**Prevention:**
- Enable Spot interruption handling in Karpenter
- Configure Spark for executor failure tolerance
- Use On-Demand for critical jobs
- Implement job retry logic

**Spark Configuration:**
```
spark.task.maxAttempts=4
spark.executor.allowSparkContext=true
spark.serializer=org.apache.spark.serializer.KryoSerializer
```

**Karpenter Configuration:**
- Enable `enable_spot_termination = true`
- Configure SQS queue for interruptions
- Set appropriate TTL for consolidation

### Scenario 3: Network Congestion During Shuffle

**Symptoms:**
- Slow Spark job execution
- Timeout errors during shuffle
- High network utilization

**Root Causes:**
1. Insufficient bandwidth between AZs
2. Security group rules blocking traffic
3. No NLB for shuffle traffic
4. VPC CNI not optimized

**Prevention:**
- Use NLB for shuffle service (L4 load balancing)
- Place executors in same AZ when possible (affinity rules)
- Optimize VPC CNI settings
- Use enhanced networking (SR-IOV)
- Monitor network metrics

**Network Optimization:**
- Enable VPC CNI custom networking
- Use placement groups for Spark nodes
- Configure NLB with cross-zone load balancing disabled (for same-AZ)

### Scenario 4: Out of IP Addresses

**Symptoms:**
- Pods cannot be scheduled
- "Insufficient IP addresses" errors
- Nodes show IP exhaustion

**Root Causes:**
1. VPC CNI not configured for large pod counts
2. Subnet CIDR too small
3. Too many nodes in single subnet

**Prevention:**
- Use custom networking mode (VPC CNI)
- Enable prefix delegation
- Distribute nodes across multiple subnets
- Monitor IP address usage

**VPC CNI Configuration:**
```
WARM_ENI_TARGET=2
WARM_IP_TARGET=10
ENABLE_PREFIX_DELEGATION=true
```

### Scenario 5: Karpenter Over-Provisioning

**Symptoms:**
- Too many nodes created
- High AWS costs
- Nodes underutilized

**Root Causes:**
1. TTL too high
2. Consolidation disabled
3. Resource requests too large
4. Multiple NodePools matching same pods

**Prevention:**
- Set appropriate TTL (60-120s for Spark)
- Enable consolidation policy
- Right-size resource requests
- Use node selectors to target specific pools
- Monitor node utilization

### Scenario 6: Spark Driver Pod Fails

**Symptoms:**
- Job fails immediately
- No executors started
- Driver pod in CrashLoopBackOff

**Root Causes:**
1. Resource requests too large
2. Image pull failures
3. Configuration errors
4. IAM permissions for driver

**Prevention:**
- Use appropriate resource requests for driver
- Test images before deployment
- Validate Spark configurations
- Ensure driver service account has correct IRSA

---

## 5. Validation, Monitoring, and Debugging

### Pre-Deployment Validation

**1. Validate Terraform State:**
```bash
# Check remote state configuration
terraform workspace list
terraform workspace select <workspace>
terraform state list

# Validate module dependencies
terraform validate
terraform plan -detailed-exitcode
```

**2. Validate IAM Roles:**
```bash
# Karpenter IRSA role
aws iam get-role --role-name <karpenter-role>
aws iam list-attached-role-policies --role-name <karpenter-role>

# Node instance profile
aws iam get-instance-profile --instance-profile-name <node-profile>
```

**3. Validate Network:**
```bash
# Subnet tags
aws ec2 describe-subnets \
  --filters "Name=tag:karpenter.sh/discovery,Values=<cluster-name>" \
  --query 'Subnets[*].[SubnetId,Tags[?Key==`karpenter.sh/discovery`].Value]'

# Security group tags
aws ec2 describe-security-groups \
  --filters "Name=tag:karpenter.sh/discovery,Values=<cluster-name>"

# VPC endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=<vpc-id>"
```

**4. Validate EKS Cluster:**
```bash
# Cluster status
aws eks describe-cluster --name <cluster-name> --query 'cluster.status'

# OIDC provider
aws eks describe-cluster --name <cluster-name> --query 'cluster.identity.oidc.issuer'

# Node groups
aws eks list-nodegroups --cluster-name <cluster-name>
```

**5. Validate Karpenter Installation:**
```bash
# Karpenter deployment
kubectl get deployment -n karpenter karpenter

# Karpenter pods
kubectl get pods -n karpenter

# NodePools
kubectl get nodepools

# EC2NodeClasses
kubectl get ec2nodeclasses
```

### Post-Deployment Validation

**1. Test Node Provisioning:**
```bash
# Create test pod with resource requests
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: test-karpenter
spec:
  nodeSelector:
    spark-workload: "true"
  containers:
  - name: test
    image: busybox
    command: ["sleep", "300"]
    resources:
      requests:
        cpu: 2000m
        memory: 4Gi
EOF

# Watch node provisioning
watch kubectl get nodes -L spark-workload,workload-type

# Check Karpenter logs
kubectl logs -n karpenter -l app.kubernetes.io/name=karpenter -c controller -f
```

**2. Test Spark Job:**
```bash
# Submit test Spark job
kubectl apply -f spark-test-job.yaml

# Monitor job
kubectl get pods -n spark-jobs -w

# Check node provisioning
kubectl get nodes -L spark-workload --sort-by=.metadata.creationTimestamp
```

### Monitoring Setup

**1. Karpenter Metrics:**
```bash
# Enable metrics in Karpenter
# Add to Helm values:
metrics:
  port: 8080
  serviceMonitor:
    enabled: true

# Access metrics
kubectl port-forward -n karpenter svc/karpenter 8080:8080
curl http://localhost:8080/metrics
```

**Key Metrics to Monitor:**
- `karpenter_nodes_created` - Nodes provisioned
- `karpenter_nodes_terminated` - Nodes removed
- `karpenter_provisioner_limit` - Pool limits
- `karpenter_provisioner_usage` - Current usage

**2. Spark Metrics:**
- Spark UI (via ALB ingress)
- Prometheus metrics (if Spark operator configured)
- CloudWatch Container Insights

**3. Cluster Metrics:**
```bash
# Node utilization
kubectl top nodes

# Pod resource usage
kubectl top pods -n spark-jobs

# Node conditions
kubectl get nodes -o wide
```

### Debugging Procedures

**1. Pod Stuck in Pending:**
```bash
# Check pod events
kubectl describe pod <pod-name> -n <namespace>

# Check why not scheduled
kubectl get events --sort-by='.lastTimestamp' -n <namespace>

# Check Karpenter logs
kubectl logs -n karpenter -l app.kubernetes.io/name=karpenter -c controller --tail=100

# Check node claims
kubectl get nodeclaims -o yaml
```

**2. Nodes Not Being Created:**
```bash
# Check Karpenter controller logs
kubectl logs -n karpenter -l app.kubernetes.io/name=karpenter -c controller | grep -i error

# Check IAM permissions
aws sts get-caller-identity
aws ec2 describe-instances --filters "Name=tag:Name,Values=*karpenter*" --max-items 5

# Check EC2 limits
aws service-quotas get-service-quota --service-code ec2 --quota-code L-34B43A08

# Check subnet availability
aws ec2 describe-subnets --subnet-ids <subnet-id> --query 'Subnets[0].AvailableIpAddressCount'
```

**3. Spark Job Failures:**
```bash
# Check driver logs
kubectl logs <spark-driver-pod> -n spark-jobs

# Check executor logs
kubectl logs <spark-executor-pod> -n spark-jobs

# Check Spark UI (if accessible)
# Access via ALB ingress

# Check node conditions
kubectl get nodes -o yaml | grep -A 5 conditions
```

**4. Network Issues:**
```bash
# Test pod-to-pod connectivity
kubectl run test-pod --image=busybox --rm -it -- sh
# Inside pod: ping <other-pod-ip>

# Check security group rules
aws ec2 describe-security-groups --group-ids <sg-id>

# Check VPC CNI logs
kubectl logs -n kube-system -l app=vpc-cni

# Test NLB connectivity
# From pod: curl <nlb-endpoint>
```

**5. Cost Optimization:**
```bash
# List all nodes
kubectl get nodes -o wide

# Check node utilization
kubectl top nodes

# Check for underutilized nodes
# Nodes with < 30% CPU/memory utilization

# Check Karpenter consolidation
kubectl logs -n karpenter -l app.kubernetes.io/name=karpenter -c controller | grep consolidation
```

### Operational Runbooks

**1. Scale Down Spark Jobs:**
```bash
# Scale down Spark job
kubectl scale deployment <spark-deployment> --replicas=0 -n spark-jobs

# Wait for consolidation (check TTL)
kubectl get nodes -w

# Force node removal (if needed)
kubectl delete node <node-name>
```

**2. Emergency Node Provisioning:**
```bash
# If Karpenter not working, manually create node group
# Use EKS managed node group as fallback

# Or force Karpenter to provision
kubectl delete nodeclaim <nodeclaim-name>
```

**3. Spot Interruption Handling:**
```bash
# Check Spot interruption queue
aws sqs get-queue-attributes --queue-url <sqs-url> --attribute-names All

# Monitor interruptions
kubectl logs -n karpenter -l app.kubernetes.io/name=karpenter -c controller | grep interruption
```

---

## Summary: Production Checklist

### Pre-Production
- [ ] All modules deployed in correct order
- [ ] IAM roles validated
- [ ] Network tags correct (Karpenter discovery)
- [ ] VPC endpoints configured
- [ ] Security groups allow required traffic
- [ ] Karpenter NodePools configured
- [ ] EC2 limits checked
- [ ] Monitoring enabled

### Production Deployment
- [ ] Test node provisioning with sample pod
- [ ] Test Spark job submission
- [ ] Validate autoscaling behavior
- [ ] Test Spot interruption handling
- [ ] Validate network connectivity (shuffle)
- [ ] Monitor initial job runs

### Ongoing Operations
- [ ] Monitor Karpenter metrics
- [ ] Monitor Spark job success rates
- [ ] Review node utilization
- [ ] Optimize NodePool configurations
- [ ] Review costs regularly
- [ ] Update Karpenter/Spark versions

---

This architecture provides a production-grade foundation for running Spark workloads on EKS 1.33 with Karpenter autoscaling. Focus on proper module boundaries, network design, and failure prevention to ensure reliability at scale.
