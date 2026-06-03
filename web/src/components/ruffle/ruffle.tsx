import { Suspense } from 'react';
import RuffleConfig from './ruffle-config';
import RuffleLoader from './ruffle-loader';

export default function Ruffle() {
  return (
    <>
      <RuffleConfig />
      <Suspense fallback={null}>
        <RuffleLoader />
      </Suspense>
    </>
  );
}
