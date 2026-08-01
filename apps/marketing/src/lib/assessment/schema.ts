import { z } from "zod";

export const businessTypeSchema = z.object({
  businessType: z.string().min(1, "Please select a business type"),
});

export const mainProblemsSchema = z.object({
  mainProblems: z.array(z.string()).min(1, "Select at least one problem"),
});

export const currentProcessSchema = z.object({
  currentProcess: z.string().min(1, "Please select how this work is handled"),
});

export const weeklyTimeSchema = z.object({
  weeklyTimeSpent: z.string().min(1, "Please select a time range"),
});

export const peopleInvolvedSchema = z.object({
  peopleInvolved: z.string().min(1, "Please select a people range"),
});

export const contactSchema = z.object({
  contactName: z.string().min(1, "Name is required"),
  contactEmail: z.string().email("Enter a valid email"),
  contactCompany: z.string().min(1, "Company name is required"),
  contactPhone: z.string().optional(),
  additionalDetails: z.string().optional(),
});

