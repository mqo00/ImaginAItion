import React from 'react';

export default function RevealIcon() {
  return (
    <svg
      width="28"
      height="28"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"
        fill="currentColor"
      />
      {/* small twinkling stars */}
      <circle cx="8" cy="8" r="1" fill="currentColor" opacity="0.7">
        <animate attributeName="opacity" values="0.3;1;0.3" dur="1.5s" repeatCount="indefinite" />
      </circle>
      <circle cx="16" cy="8" r="0.8" fill="currentColor" opacity="0.5">
        <animate attributeName="opacity" values="0.2;0.8;0.2" dur="2s" repeatCount="indefinite" />
      </circle>
      <circle cx="18" cy="16" r="0.6" fill="currentColor" opacity="0.6">
        <animate attributeName="opacity" values="0.4;1;0.4" dur="1.8s" repeatCount="indefinite" />
      </circle>
    </svg>
  );
} 