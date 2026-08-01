import js from "@eslint/js";
import nextPlugin from "@next/eslint-plugin-next";
import globals from "globals";
import importPlugin from "eslint-plugin-import";
import jsxA11y from "eslint-plugin-jsx-a11y";
import reactPlugin from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import tseslint from "typescript-eslint";

const config = [
	{
		ignores: [".next/**", "coverage/**", "dist/**", "next-env.d.ts"]
	},
	js.configs.recommended,
	...tseslint.configs.recommended,
	{
		files: ["**/*.{js,jsx,ts,tsx,mjs,cjs}"],
		languageOptions: {
			ecmaVersion: "latest",
			sourceType: "module",
			globals: {
				...globals.browser,
				...globals.node
			}
		},
		plugins: {
			"@next/next": nextPlugin,
			import: importPlugin,
			"jsx-a11y": jsxA11y,
			react: reactPlugin,
			"react-hooks": reactHooks
		},
		settings: {
			react: {
				version: "detect"
			}
		},
		rules: {
			...reactPlugin.configs.recommended.rules,
			...reactHooks.configs.recommended.rules,
			...jsxA11y.configs.recommended.rules,
			...nextPlugin.configs.recommended.rules,
			...nextPlugin.configs["core-web-vitals"].rules,
			"import/no-anonymous-default-export": "warn",
			"react/prop-types": "off",
			"react/react-in-jsx-scope": "off"
		}
	}
];

export default config;
