import { Construct } from "constructs";
import * as cdk from "aws-cdk-lib";
import { addManagedPolicies } from "./utils";
import { Bucket } from "aws-cdk-lib/aws-s3";
import { Role, ServicePrincipal } from "aws-cdk-lib/aws-iam";
import { Runtime, Function, Code, LayerVersion } from "aws-cdk-lib/aws-lambda";
import * as apigateway from "aws-cdk-lib/aws-apigateway";

interface ScrapeTwitterProps {
  api: apigateway.RestApi;
}

export class ScrapeTwitter extends Construct {
  constructor(scope: Construct, id: string, props: ScrapeTwitterProps) {
    super(scope, id);

    const { api } = props;

    // create s3 bucket and make it publick
    const bucket = new Bucket(this, "TwitterScrapBucket", {
      autoDeleteObjects: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const lambdaRole = new Role(this, "LambdaRole", {
      assumedBy: new ServicePrincipal("lambda.amazonaws.com"),
    });

    addManagedPolicies(lambdaRole, [
      "AmazonS3FullAccess",
      "service-role/AWSLambdaBasicExecutionRole",
      "CloudWatchFullAccess",
    ]);
    // Create the Lambda Layer
    const layer = new LayerVersion(this, "scrapeTwitterLayer", {
      code: Code.fromAsset("layers/scrapeTwitter/lambda_layers/layer.zip"),
      compatibleRuntimes: [Runtime.PYTHON_3_8],
      license: "Apache-2.0",
      description: "A layer containing required Python packages for twitter scraping",
    });

    const pandas = LayerVersion.fromLayerVersionArn(
      this,
      "Pandas",
      `arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p38-pandas:13`
    );

    const openpyxl = LayerVersion.fromLayerVersionArn(
      this,
      "Openpyxl",
      `arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p38-openpyxl:3`
    );

    // const numpy = LayerVersion.fromLayerVersionArn(
    //   this,
    //   "Numpy",
    //   `	arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p38-numpy:12`
    // );

    const twiterScrapeLambda = new Function(this, "TwitterScrapeLambda", {
      runtime: Runtime.PYTHON_3_8,
      handler: "index.handler",
      code: Code.fromAsset("src/scrapeTwitter"),
      role: lambdaRole,
      environment: {
        BUCKET_NAME: bucket.bucketName,
      },
      layers: [layer, pandas, openpyxl],
      timeout: cdk.Duration.seconds(900),
      memorySize: 1024,
    });

    bucket.grantReadWrite(twiterScrapeLambda);
    bucket.grantPutAcl(twiterScrapeLambda);

    const scrapeTwitterIntegration = new apigateway.LambdaIntegration(twiterScrapeLambda);
    const scrapeTwitterResource = api.root.addResource("scrape-twitter");
    scrapeTwitterResource.addMethod("GET", scrapeTwitterIntegration);
  }
}
