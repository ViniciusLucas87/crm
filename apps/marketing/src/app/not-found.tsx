import { Container } from "@/components/ui/container";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="min-h-[70vh] flex items-center">
      <Container>
        <div className="max-w-lg mx-auto text-center py-20">
          <p className="text-sm font-medium text-pns-text-muted tracking-wide uppercase">
            404
          </p>
          <h1 className="mt-4 text-3xl font-bold text-pns-text-primary">
            Page not found
          </h1>
          <p className="mt-4 text-pns-text-muted leading-relaxed">
            The page you&apos;re looking for doesn&apos;t exist or has been
            moved. Let&apos;s get you back on track.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
            <Button variant="primary" href="/">
              Back to Home
            </Button>
            <Button variant="outline" href="/solutions">
              Explore Solutions
            </Button>
          </div>
        </div>
      </Container>
    </main>
  );
}
