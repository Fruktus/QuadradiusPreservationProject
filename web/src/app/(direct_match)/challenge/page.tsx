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
  url: string;
};

// Error responses from the backend are:
//
// {
//   "error": "some message"
// }
type ApiError = {
  error: string;
};

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
  const [swfUrl, setSwfUrl] = useState<string | null>(null);
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
          `/api/v1/invites/${inviteId}/make-url`
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
        setSwfUrl(data.url);
        setStatus('game');
      } catch (error) {
        // FIXME leave the status untemplated, log to console
        setErrorMessage(
          `Something went wrong while loading the challenge: ${error}`
        );
        setStatus('error');
      }
    };


    fetchInvite();
  },  [inviteId]);


  // ------------------------------------------------------------
  // LOADING
  // ------------------------------------------------------------
  if (status === 'loading') {
    return (
      <MessagePanel
        message="Loading challenge..."
        variant="busy"
      />
    );
  }


  // ------------------------------------------------------------
  // EXPIRED
  // ------------------------------------------------------------
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


  // ------------------------------------------------------------
  // OTHER ERROR
  // ------------------------------------------------------------
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


  // ------------------------------------------------------------
  // SAFETY CHECK
  // ------------------------------------------------------------
  // We should only reach the "game" state when swfUrl exists,
  // because we set swfUrl before setting status to "game".
  //
  // This just protects us from accidentally rendering an invalid
  // <embed> URL if the state ever gets into an unexpected state.
  if (!swfUrl) {
    return (
      <MessagePanel
        message="Game URL is missing."
        variant="error"
      />
    );
  }


  // ------------------------------------------------------------
  // GAME
  // ------------------------------------------------------------
  const gameUrl = `/quadradius_game.swf?${swfUrl}`;


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
