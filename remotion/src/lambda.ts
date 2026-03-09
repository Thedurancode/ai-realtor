/**
 * Remotion Lambda — cloud rendering configuration.
 *
 * Deploys Remotion to AWS Lambda for scalable video rendering.
 * Each render runs as an isolated Lambda invocation — no server needed.
 *
 * Setup steps:
 * 1. Set AWS credentials: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
 * 2. Set REMOTION_AWS_REGION (default: us-east-1)
 * 3. Run: npx remotion lambda policies role  (creates IAM role)
 * 4. Run: npx remotion lambda sites create src/index.tsx --site-name=ai-realtor
 * 5. Run: npx remotion lambda functions deploy --memory=2048 --timeout=240
 *
 * Usage from Python backend (app/services/video_render_service.py):
 *   POST /api/v1/videos/render-lambda with compositionId + inputProps
 */

import {
  renderMediaOnLambda,
  getRenderProgress,
  deploySite,
  deployFunction,
  getOrCreateBucket,
} from "@remotion/lambda";
import { bundle } from "@remotion/bundler";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

// Config from environment
const REGION = (process.env.REMOTION_AWS_REGION || "us-east-1") as
  | "us-east-1"
  | "us-east-2"
  | "us-west-2"
  | "eu-central-1"
  | "eu-west-1"
  | "ap-southeast-1";
const SITE_NAME = process.env.REMOTION_SITE_NAME || "ai-realtor";
const FUNCTION_NAME = process.env.REMOTION_FUNCTION_NAME || undefined;
const MEMORY_SIZE = parseInt(process.env.REMOTION_LAMBDA_MEMORY || "2048", 10);
const TIMEOUT = parseInt(process.env.REMOTION_LAMBDA_TIMEOUT || "240", 10);

/**
 * Deploy the Remotion site to S3 (run once or on code changes).
 */
export async function deploySiteToS3() {
  console.log("Bundling Remotion project...");
  const bundleLocation = await bundle({
    entryPoint: join(__dirname, "index.tsx"),
  });

  const { bucketName } = await getOrCreateBucket({ region: REGION });

  console.log(`Deploying site to S3 bucket: ${bucketName}...`);
  const { serveUrl } = await deploySite({
    bucketName,
    entryPoint: bundleLocation,
    region: REGION,
    siteName: SITE_NAME,
  });

  console.log(`Site deployed: ${serveUrl}`);
  return { serveUrl, bucketName };
}

/**
 * Deploy the Lambda function (run once or when updating Lambda config).
 */
export async function deployLambdaFunction() {
  console.log(`Deploying Lambda function (${MEMORY_SIZE}MB, ${TIMEOUT}s timeout)...`);
  const { functionName, alreadyExisted } = await deployFunction({
    region: REGION,
    timeoutInSeconds: TIMEOUT,
    memorySizeInMb: MEMORY_SIZE,
    createCloudWatchLogGroup: true,
  });

  console.log(
    alreadyExisted
      ? `Lambda function already exists: ${functionName}`
      : `Lambda function deployed: ${functionName}`
  );
  return functionName;
}

/**
 * Render a video on Lambda.
 *
 * @param compositionId - e.g. "PropertyShowcase", "CinematicEventRecap"
 * @param inputProps - props to pass to the composition
 * @param codec - "h264" (default) or "h265"
 */
export async function renderOnLambda(
  compositionId: string,
  inputProps: Record<string, any>,
  codec: "h264" | "h265" = "h264"
) {
  const { bucketName } = await getOrCreateBucket({ region: REGION });

  const { renderId, bucketName: renderBucket } = await renderMediaOnLambda({
    region: REGION,
    functionName: FUNCTION_NAME || (await deployLambdaFunction()),
    serveUrl: `https://${bucketName}.s3.${REGION}.amazonaws.com/sites/${SITE_NAME}/index.html`,
    composition: compositionId,
    inputProps,
    codec,
    imageFormat: "jpeg",
    maxRetries: 1,
    framesPerLambda: 20,
    privacy: "public",
  });

  return { renderId, bucketName: renderBucket };
}

/**
 * Check render progress.
 */
export async function checkRenderProgress(renderId: string, bucketName: string) {
  const progress = await getRenderProgress({
    renderId,
    bucketName,
    region: REGION,
    functionName: FUNCTION_NAME || "",
  });

  return {
    done: progress.done,
    overallProgress: progress.overallProgress,
    outputFile: progress.outputFile,
    errors: progress.errors,
    fatalErrorEncountered: progress.fatalErrorEncountered,
  };
}

// CLI entry point — deploy site + function
if (process.argv[1]?.includes("lambda")) {
  const command = process.argv[2];

  if (command === "deploy-site") {
    deploySiteToS3().catch(console.error);
  } else if (command === "deploy-function") {
    deployLambdaFunction().catch(console.error);
  } else if (command === "deploy-all") {
    (async () => {
      await deploySiteToS3();
      await deployLambdaFunction();
      console.log("All deployed. Ready to render on Lambda.");
    })().catch(console.error);
  } else {
    console.log("Usage: npx tsx src/lambda.ts [deploy-site|deploy-function|deploy-all]");
  }
}
