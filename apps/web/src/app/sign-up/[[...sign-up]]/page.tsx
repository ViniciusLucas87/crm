import { redirect } from "next/navigation";

export default function SignUpPage() {
  // Owners provision CRM accounts through Clerk; public registration is closed.
  redirect("/sign-in");
}
