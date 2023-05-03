import { Construct } from "constructs";
import * as cdk from "aws-cdk-lib";
import { addManagedPolicies } from "./utils";
import { Role, ServicePrincipal } from "aws-cdk-lib/aws-iam";
import { Runtime, Function, Code, LayerVersion } from "aws-cdk-lib/aws-lambda";
import * as apigateway from "aws-cdk-lib/aws-apigateway";

interface CompetitiveAnalysisProps {
  api: apigateway.RestApi;
}

export class CompetitiveAnalysis extends Construct {
  constructor(scope: Construct, id: string, props: CompetitiveAnalysisProps) {
    super(scope, id);

    const { api } = props;

    const lambdaRole = new Role(this, "LambdaRole", {
      assumedBy: new ServicePrincipal("lambda.amazonaws.com"),
    });

    addManagedPolicies(lambdaRole, [
      "service-role/AWSLambdaBasicExecutionRole",
      "CloudWatchFullAccess",
    ]);

    const pandas = LayerVersion.fromLayerVersionArn(
      this,
      "Pandas",
      `arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p38-pandas:13`
    );
    const layer = new LayerVersion(this, "scrapeTwitterLayer", {
      code: Code.fromAsset("layers/competitiveAnalysis/lambda_layers/layer.zip"),
      compatibleRuntimes: [Runtime.PYTHON_3_8],
      license: "Apache-2.0",
      description: "A layer containing required Python packages for twitter scraping",
    });

    const openpyxl = LayerVersion.fromLayerVersionArn(
      this,
      "Openpyxl",
      `arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p38-openpyxl:4`
    );

    const twiterScrapeLambda = new Function(this, "CompetitiveAnalysisLambda", {
      runtime: Runtime.PYTHON_3_8,
      handler: "index.handler",
      code: Code.fromAsset("src/competitiveAnalysis"),
      role: lambdaRole,
      layers: [pandas, layer, openpyxl],
      timeout: cdk.Duration.seconds(900),
      memorySize: 1024,
    });

    const CompetitiveAnalysisIntegration = new apigateway.LambdaIntegration(twiterScrapeLambda);
    const CompetitiveAnalysisResource = api.root.addResource("competitive-analysis");
    CompetitiveAnalysisResource.addMethod("POST", CompetitiveAnalysisIntegration);
  }
}
