'use client';

import Image from 'next/image';
import { useEffect, useRef } from 'react';
import styles from './fullscreen-toggle.module.css';

export default function FullscreenToggle() {
    const openIconRef = useRef<HTMLImageElement>(null);
    const closeIconRef = useRef<HTMLImageElement>(null);

    useEffect(() => {
        const openIcon = openIconRef.current;
        const closeIcon = closeIconRef.current;
        if (!openIcon || !closeIcon) return;

        closeIcon.style.display = 'none';

        const updateIcons = (isFullscreen: boolean) => {
            openIcon.style.display = isFullscreen ? 'none' : 'block';
            closeIcon.style.display = isFullscreen ? 'block' : 'none';
        };

        const handleFullscreenChange = () => updateIcons(!!document.fullscreenElement);
        document.addEventListener('fullscreenchange', handleFullscreenChange);
        return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
    }, []);

    const handleClick = () => {
        if (!document.fullscreenElement) {
            void document.documentElement.requestFullscreen();
        } else {
            void document.exitFullscreen();
        }
    };

    return (
        <div className={styles.fullscreen}>
            <button className={styles.toggle} title="Toggle fullscreen" onClick={handleClick}>
                <Image ref={openIconRef} src="/fullscreen-open.svg" alt="Fullscreen open icon" fill />
                <Image ref={closeIconRef} src="/fullscreen-close.svg" alt="Fullscreen close icon" fill />
            </button>
        </div>
    );
}
