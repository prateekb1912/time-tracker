"use client";

import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 p-6">
      <h1 className="text-4xl font-bold mb-4 text-center">
        Welcome to T3 Time Tracker
      </h1>
      <p className="mb-6 text-center text-gray-700 max-w-xl">
        You’ve been invited to join the T3 platform. Please verify your account
        to activate and download the time tracking app.
      </p>
      <Link href="/activate">
        <button className="bg-blue-600 text-white px-6 py-2 rounded-xl shadow hover:bg-blue-700">
          Verify Your Email
        </button>
      </Link>
    </div>
  );
}
