/**
 * Note: When using the Node.JS APIs, the config file
 * doesn't apply. Instead, pass options directly to the APIs.
 *
 * All configuration options: https://remotion.dev/docs/config
 */

import { Config } from "@remotion/cli/config";
import { enableTailwind } from '@remotion/tailwind-v4';

// Performance optimizations - prevents CPU/RAM spikes
Config.setRspack(true);
Config.setConcurrency(2);  // Lower concurrency for smoother performance on laptops
Config.setVideoImageFormat("jpeg");  // Faster than PNG
Config.setAudioCodec("aac");  // Faster encoding
Config.setOverwriteOutput(true);
Config.setChromiumMultiProcessOnLinux(true);  // Better parallel processing
Config.setCachingEnabled(true);  // Cache bundles for faster subsequent renders
Config.setDisallowParallelEncoding(false);  // Encode while rendering
Config.overrideBundlerConfig(enableTailwind);
