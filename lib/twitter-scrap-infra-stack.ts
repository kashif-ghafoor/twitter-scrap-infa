import * as cdk from "aws-cdk-lib";
import { ApiGateway } from "aws-cdk-lib/aws-events-targets";
import { Construct } from "constructs";
import * as apigateway from "aws-cdk-lib/aws-apigateway";
import { ScrapeTwitter } from "./scrapeTwitter";
import { CompetitiveAnalysis } from "./competitiveAnalysis";
import { HashtagAnalysis } from "./hashtagAnalysis";

// import * as sqs from 'aws-cdk-lib/aws-sqs';

export class TwitterScrapInfraStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const api = new apigateway.RestApi(this, "tweets-analysis", {
      restApiName: "Tweet Analysis Service",
      description: "This service serves twitter scraping and analysis",
      deployOptions: {
        stageName: "prod",
      },
      defaultCorsPreflightOptions: {
        allowHeaders: [
          "Content-Type",
          "X-Amz-Date",
          "Authorization",
          "X-Api-Key",
          "multipart/form-data",
        ],
        allowMethods: ["GET", "POST"],
        allowCredentials: true,
        allowOrigins: ["*"],
      },
      binaryMediaTypes: ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
    });

    new ScrapeTwitter(this, "ScrapeTwitter", {
      api,
    });

    new CompetitiveAnalysis(this, "CompetitiveAnalysis", {
      api,
    });

    new HashtagAnalysis(this, "HashtagAnalysis", {
      api,
    });
  }
}
