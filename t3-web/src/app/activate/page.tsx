"use client";

import { useState } from "react";

export default function Activate() {
  const [activated, setActivated] = useState(false);

  const handleActivate = () => {
    setTimeout(() => setActivated(true), 1000);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-white p-6">
      {!activated ? (
        <>
          <h2 className="text-2xl font-semibold mb-4">Activate Your Account</h2>
          <p className="mb-4 text-gray-600 text-center max-w-md">
            Click the button below to verify your email and activate your
            account.
          </p>
          <button
            onClick={handleActivate}
            className="bg-green-600 text-white px-6 py-2 rounded-xl shadow hover:bg-green-700"
          >
            Activate Account
          </button>
        </>
      ) : (
        <>
          <h2 className="text-2xl font-semibold mb-4 text-green-700">
            Account Activated!
          </h2>
          <p className="mb-4 text-gray-700 text-center max-w-md">
            Your account is now active. You can now download the T3 desktop time
            tracking app.
          </p>
          <a
            href="https://example.com/download"
            className="bg-blue-600 text-white px-6 py-2 rounded-xl shadow hover:bg-blue-700"
          >
            Download App
          </a>
        </>
      )}
    </div>
  );
}
