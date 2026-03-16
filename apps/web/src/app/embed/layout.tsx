/**
 * Embed layout — no navbar, no auth provider.
 * Minimal chrome for iframe embedding.
 */
export default function EmbedLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-black text-white m-0 p-0">{children}</body>
    </html>
  );
}
