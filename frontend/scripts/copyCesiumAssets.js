import { cp, mkdir, rm } from 'node:fs/promises';
import { resolve } from 'node:path';

const root = process.cwd();
const cesiumSource = resolve(root, 'node_modules/cesium/Build/Cesium');
const cesiumTarget = resolve(root, 'public/cesium');
const directories = ['Assets', 'ThirdParty', 'Widgets', 'Workers'];

async function copyCesiumAssets() {
  console.log('Preparing Cesium runtime assets...');

  await rm(cesiumTarget, { recursive: true, force: true });
  await mkdir(cesiumTarget, { recursive: true });

  for (const directory of directories) {
    const source = resolve(cesiumSource, directory);
    const target = resolve(cesiumTarget, directory);
    await cp(source, target, { recursive: true });
    console.log(`Copied Cesium ${directory}`);
  }

  console.log('Cesium runtime assets ready at public/cesium.');
}

copyCesiumAssets().catch((error) => {
  console.error('Failed to copy Cesium runtime assets.');
  console.error(error);
  process.exit(1);
});
