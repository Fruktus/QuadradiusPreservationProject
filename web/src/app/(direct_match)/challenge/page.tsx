'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';

import Footer from '@/components/ui/footer/footer';
import Ruffle from '@/components/ruffle/ruffle';
import FullscreenToggle from '@/components/ui/fullscreen-toggle/fullscreen-toggle';
import MessagePanel from '@/components/ui/message-panel';

import { useUnloadWarning } from '@/hooks/use-unload-warning';
import { apiFetch } from '@/lib/api';


type Status = 'loading' | 'game' | 'expired' | 'error';


// The successful response from:
// GET /api/v1/invites/{invite_id}
// is:
// {
//   "url": "myName=...&myAuthentication=...&..."
// }
type InviteSuccess = {
  params: string;
};

// Error responses from the backend are:
//
// {
//   "error": "some message"
// }
type ApiError = {
  error: string;
};

// Since we need access to searchParams, we need Suspense boundary wrapper
export default function DirectChallengeWrapper() {
  return (
    <Suspense fallback={<MessagePanel message="Loading challenge..." variant="busy" />}>
      <DirectChallenge />
    </Suspense>
  );
}


function DirectChallenge() {
  useUnloadWarning();
  const [status, setStatus] = useState<Status>('loading');
  const [swfParams, setSwfParams] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const searchParams = useSearchParams();
  const inviteId = searchParams.get('id');

  useEffect(() => {
      if (!inviteId) {
        setErrorMessage(
          'Missing Invite ID'
        );
        setStatus('error');
        return;
      }

    const fetchInvite = async () => {
      try {
        const response = await apiFetch(
          `/api/v1/invites/${inviteId}/make-params`
        );

        if (response.status === 410) {
          const data: ApiError = await response.json();

          setErrorMessage(data.error);
          setStatus('expired');

          return;
        }

        if (!response.ok) {
          const data: ApiError = await response.json();

          setErrorMessage(
            data.error || 'Something went wrong.'
          );

          setStatus('error');

          return;
        }

        const data: InviteSuccess = await response.json();
        setSwfParams(data.params);
        setStatus('game');
      } catch (error) {
        setErrorMessage('Something went wrong while loading the challenge');
        setStatus('error');
        console.error(`invite join failed: ${error}`)
      }
    };


    fetchInvite();
  },  [inviteId]);

  if (status === 'loading') {
    return (
      <MessagePanel
        message="Loading challenge..."
        variant="busy"
      />
    );
  }

  if (status === 'expired') {
    return (
      <MessagePanel
        message={
          errorMessage ?? 'This challenge has expired.'
        }
        variant="error"
      />
    );
  }

  if (status === 'error') {
    return (
      <MessagePanel
        message={
          errorMessage ??
          'Something went wrong while loading the challenge.'
        }
        variant="error"
      />
    );
  }

  if (!swfParams) {
    return (
      <MessagePanel
        message="Game Params is missing."
        variant="error"
      />
    );
  }

  const gameUrl = `/quadradius_game.swf?${swfParams}`;

  return (
    <>
      <Ruffle />
      <FullscreenToggle />
      <div className="game-container">
        <object className="game">
          <embed
            src={gameUrl}
            className="embed"
          />
        </object>
        <Footer />
      </div>
    </>
  );
}