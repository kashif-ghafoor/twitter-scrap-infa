import * as iam from "aws-cdk-lib/aws-iam";

export function addManagedPolicies(role: iam.Role, policyNames: string[]) {
  policyNames.forEach((policyName) => {
    role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName(policyName));
  });
}
