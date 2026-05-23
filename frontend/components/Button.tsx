import clsx from "clsx";
import { ButtonHTMLAttributes, forwardRef } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger" | "ghost";
};

const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { variant = "primary", className, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      className={clsx(
        "inline-flex items-center justify-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed",
        {
          "bg-neutral-900 text-white hover:bg-neutral-800": variant === "primary",
          "bg-white text-neutral-900 border border-neutral-200 hover:bg-neutral-50":
            variant === "secondary",
          "bg-red-600 text-white hover:bg-red-700": variant === "danger",
          "text-neutral-700 hover:bg-neutral-100": variant === "ghost",
        },
        className,
      )}
      {...rest}
    />
  );
});

export default Button;
