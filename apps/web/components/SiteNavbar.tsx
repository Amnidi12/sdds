import Link from "next/link";

export default function SiteNavbar() {
  return (
    <header className="border-b border-gray-200 dark:border-gray-800">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-brand-600 text-sm font-medium text-white">
            S
          </div>
          <span className="text-sm font-semibold">Smart Donation Tracker</span>
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/track" className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
            Track a Donation
          </Link>
          <Link href="/login" className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
            Log in
          </Link>
          <Link href="/register" className="rounded-md bg-brand-600 px-4 py-2 font-medium text-white hover:bg-brand-700">
            Get Started
          </Link>
        </nav>
      </div>
    </header>
  );
}
