# Rollback Procedure Checklist

Follow this checklist when a critical KPI violation (severity >= 4) is detected post-deployment.

Reference: `ai-qa-core-framework/02_operations/rollback_procedure.md`

## 1. Detection & Alerting

- [ ] KPI violation detected by harness `--gate block`
- [ ] Alert triggered via `harness monitor alerts`
- [ ] On-call engineer acknowledged

## 2. Initial Response

- [ ] Verify alert is not a false positive
- [ ] Confirm affected evaluation scope
- [ ] Check dashboard for trend: `harness monitor dashboard`

## 3. Rollback Execution

- [ ] Halt all ongoing deployments
- [ ] Identify last known good version from time series history
- [ ] Execute rollback to last good version
- [ ] Validate rollback with `harness eval --limit 5`

## 4. Notification

- [ ] Release manager notified
- [ ] Platform owner notified
- [ ] Post-mortem triggered (48h SLA for severity >= 4)

## Regular Drills

- [ ] Monthly: verify detection pipeline works end-to-end
- [ ] Monthly: test alert routing reaches on-call
- [ ] Quarterly: practice rollback execution under time pressure
