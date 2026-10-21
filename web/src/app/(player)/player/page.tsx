'use client';

import { Suspense, useEffect, useState, type ComponentProps, type ReactNode } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

import MessagePanel from '@/components/ui/message-panel';
import MetalPanelScrewed from '@/components/ui/metal-panel-screwed';

import { getLoggedInUsername, loginUrlWithRedirect } from '@/lib/auth';
import { formatDate, formatDuration, formatPercent } from '@/lib/format';
import { fetchPlayerProfile, playerProfileHref, type PlayerProfile, type Trophy } from '@/lib/player';

type State =
  | { status: 'loading' }
  | { status: 'ok'; profile: PlayerProfile }
  | { status: 'not_found' }
  | { status: 'error' };

// Centering helper
function PlayerMessage(props: ComponentProps<typeof MessagePanel>) {
  return (
    <div className="flex flex-1 items-center justify-center bg-base-500">
      <MessagePanel {...props} />
    </div>
  );
}

// Since we need access to searchParams, we need Suspense boundary wrapper
export default function PlayerPageWrapper() {
  return (
    <Suspense fallback={<PlayerMessage message="Loading player..." variant="busy" />}>
      <PlayerPage />
    </Suspense>
  );
}

function PlayerPage() {
  const requestedName = useSearchParams().get('name');
  const [state, setState] = useState<State>({ status: 'loading' });

  useEffect(() => {
    let cancelled = false;
    setState({ status: 'loading' });

    void (async () => {
      // No name given: show your own profile
      const name = requestedName ?? (await getLoggedInUsername());
      if (!name) {
        window.location.assign(loginUrlWithRedirect());
        return;
      }

      const result = await fetchPlayerProfile(name);
      if (cancelled) return;
      setState(result.status === 'ok' ? { status: 'ok', profile: result.profile } : { status: result.status });
    })();

    return () => {
      cancelled = true;
    };
  }, [requestedName]);

  switch (state.status) {
    case 'loading':
      return <PlayerMessage message="Loading player..." variant="busy" />;
    case 'not_found':
      return <PlayerMessage message="Player not found" variant="error" />;
    case 'error':
      return <PlayerMessage message="Could not load this profile" variant="error" />;
    case 'ok':
      return <Profile profile={state.profile} />;
  }
}

const sectionTitle = 'mb-2 font-rajdhani text-[14px] font-bold uppercase leading-none tracking-[2px] text-[#2b2a27]';
const well = 'rounded border border-input-border bg-input-bg shadow-input';

function Profile({ profile }: { profile: PlayerProfile }) {
  const { player, stats, trophies } = profile;
  const memberSince = player.member_since ? formatDate(player.member_since) : '';

  return (
    <div className="min-h-0 flex-1 overflow-y-auto bg-base-500 p-3 sm:p-6">
      <MetalPanelScrewed className="mx-auto w-full max-w-4xl p-5 sm:p-7">
        <div className={`${well} flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 px-4 py-3`}>
          <h1 className="min-w-0 break-words font-dotmatrix text-2xl tracking-wide text-input-text">
            {player.username}
          </h1>
          {memberSince && (
            <span className="font-rajdhani text-[12px] font-bold uppercase tracking-[2px] text-[#b97070]">
              Member since {memberSince}
            </span>
          )}
        </div>

        <div className="mt-5 grid gap-5 md:grid-cols-2">
          <section aria-labelledby="stats-title">
            <h2 id="stats-title" className={sectionTitle}>
              Stats
            </h2>
            <dl className="flex flex-col gap-1.5">
              <StatRow label="Matches" value={String(stats.total_matches)} />
              <StatRow label="Wins / Losses" value={`${stats.wins} / ${stats.losses}`} />
              <StatRow label="Win rate" value={stats.win_rate === null ? '—' : formatPercent(stats.win_rate)} />
              <StatRow
                label="Longest match"
                value={stats.longest_match_seconds === null ? '—' : formatDuration(stats.longest_match_seconds)}
              />
              <StatRow label="Most moves" value={stats.most_moves === null ? '—' : String(stats.most_moves)} />
              <StatRow
                label="Biggest win"
                value={stats.biggest_win_margin === null ? '—' : `+${stats.biggest_win_margin} pieces`}
              />
              <StatRow
                label="Nemesis"
                value={
                  stats.nemesis ? (
                    <>
                      <Link
                        href={playerProfileHref(stats.nemesis.username)}
                        className="break-all !text-[#ff6a6a] underline-offset-2 hover:!text-[#ffaaaa] hover:underline"
                      >
                        {stats.nemesis.username}
                      </Link>{' '}
                      <span className="text-[13px] text-[#b97070]">({stats.nemesis.losses} wins)</span>
                    </>
                  ) : (
                    '—'
                  )
                }
              />
            </dl>
            <p className="mt-2 font-rajdhani text-[12px] font-bold tracking-wide text-[#2b2a27]/80">
              Only ranked matches count. A nemesis needs at least 5 wins against you.
            </p>
          </section>

          <section aria-labelledby="trophies-title">
            <h2 id="trophies-title" className={sectionTitle}>
              Trophies
            </h2>
            {trophies.length === 0 ? (
              <div className={`${well} px-3 py-6 text-center font-dotmatrix text-lg text-[#b97070]`}>
                no trophies yet
              </div>
            ) : (
              <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {trophies.map((trophy) => (
                  <TrophyTile key={trophy.id} trophy={trophy} />
                ))}
              </ul>
            )}
          </section>
        </div>
      </MetalPanelScrewed>
      <p className="mx-auto mt-3 max-w-4xl text-center font-rajdhani text-[11px] font-bold tracking-wide text-[#777]">
        Profiles are updated periodically, so recent matches and trophies may take a few minutes to show up.
      </p>
    </div>
  );
}

function StatRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className={`${well} flex items-baseline justify-between gap-3 px-3 py-1.5`}>
      <dt className="shrink-0 font-rajdhani text-[12px] font-bold uppercase tracking-[1px] text-[#b97070]">{label}</dt>
      <dd className="m-0 min-w-0 text-right font-dotmatrix text-lg leading-tight text-input-text">{value}</dd>
    </div>
  );
}

function TrophyTile({ trophy }: { trophy: Trophy }) {
  const awarded = trophy.awarded_at ? formatDate(trophy.awarded_at) : '';
  return (
    <li
      title={awarded ? `${trophy.name} (${awarded})` : trophy.name}
      className={`${well} flex flex-col items-center gap-1.5 px-2 py-3`}
    >
      {/* The SVG is admin-supplied, so it is only ever rendered through <img>, where scripts can't run. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={trophy.image} alt="" className="h-16 w-16 object-contain" />
      <span className="break-words text-center font-rajdhani text-[12px] font-bold uppercase leading-tight tracking-[1px] text-input-text">
        {trophy.name}
      </span>
    </li>
  );
}
