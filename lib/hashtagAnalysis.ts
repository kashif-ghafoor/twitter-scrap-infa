import { Construct } from "constructs";
import * as cdk from "aws-cdk-lib";
import { addManagedPolicies } from "./utils";
import { Role, ServicePrincipal } from "aws-cdk-lib/aws-iam";
import { Runtime, Function, Code, LayerVersion } from "aws-cdk-lib/aws-lambda";
import * as apigateway from "aws-cdk-lib/aws-apigateway";

interface HashtagAnalysisProps {
  api: apigateway.RestApi;
}

export class HashtagAnalysis extends Construct {
  constructor(scope: Construct, id: string, props: HashtagAnalysisProps) {
    super(scope, id);

    const { api } = props;

    const lambdaRole = new Role(this, "LambdaRole", {
      assumedBy: new ServicePrincipal("lambda.amazonaws.com"),
    });

    addManagedPolicies(lambdaRole, [
      "service-role/AWSLambdaBasicExecutionRole",
      "CloudWatchFullAccess",
    ]);

    const layer = new LayerVersion(this, "scrapeTwitterLayer", {
      code: Code.fromAsset("layers/hashtagAnalysis/lambda_layers/layer.zip"),
      license: "Apache-2.0",
      description: "A layer containing required Python packages for hashtag analysis",
    });

    const hashtagLambda = new Function(this, "hashtagAnalysisLambda", {
      runtime: Runtime.PYTHON_3_9,
      handler: "index.handler",
      code: Code.fromAsset("src/hashtagAnalysis"),
      role: lambdaRole,
      layers: [layer],
      timeout: cdk.Duration.seconds(900),
      memorySize: 1024,
    });

    const hashtagAnalysisIntegration = new apigateway.LambdaIntegration(hashtagLambda);
    const hashtagAnalysisResource = api.root.addResource("hashtag-analysis");
    hashtagAnalysisResource.addMethod("POST", hashtagAnalysisIntegration);
  }
}
