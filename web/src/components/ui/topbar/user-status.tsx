'use client';

import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import { getLoggedInUsername, getUserManager, loginUrlWithRedirect } from '@/lib/auth';
import { cn } from '@/lib/utils';
import { topbarBtn, topbarItemSize } from '@/components/ui/topbar/topbar-button';

export default function UserStatus() {
  // undefined = not read yet (server render / first paint), so the bar doesn't flash "not logged in"
  const [username, setUsername] = useState<string | null | undefined>(undefined);
  const pathname = usePathname();

  useEffect(() => {
    let cancelled = false;
    void getLoggedInUsername().then((name) => {
      if (!cancelled) setUsername(name);
    });
    return () => {
      cancelled = true;
    };
  }, [pathname]);

  // The login page is the place to log in; nothing to show there.
  if (username === undefined || pathname.startsWith('/login')) return null;

  const loggedIn = username !== null;

  // Signs out in place
  const logout = async () => {
    try {
      await getUserManager().removeUser();
    } finally {
      setUsername(null);
    }
  };
  const login = () => window.location.assign(loginUrlWithRedirect());

  return (
    <div className="flex min-w-0 items-center gap-1.5">
      <span
        title={loggedIn ? `Logged in as ${username}` : 'Not logged in'}
        className={cn(
          "flex min-w-0 items-center sm:max-w-[16rem]",
          topbarItemSize,
          "px-2 pt-px",
          "border border-input-border bg-input-bg shadow-input",
          "font-dotmatrix text-[13px] leading-none tracking-wide",
          loggedIn ? "text-input-text" : "text-[#b52a2a]",
        )}
      >
        <span className="truncate">{loggedIn ? username : 'not logged in'}</span>
      </span>
      <button type="button" className={topbarBtn} onClick={loggedIn ? () => void logout() : login}>
        {loggedIn ? 'Logout' : 'Login'}
      </button>
    </div>
  );
}
