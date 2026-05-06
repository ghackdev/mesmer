import Link from 'next/link';
import type { AnchorHTMLAttributes, ButtonHTMLAttributes, ReactNode } from 'react';

type BaseButtonProps = {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'ghost';
  className?: string;
};

type LinkButtonProps = BaseButtonProps & {
  href: string;
} & Omit<AnchorHTMLAttributes<HTMLAnchorElement>, keyof BaseButtonProps | 'href'>;

type NativeButtonProps = BaseButtonProps & {
  href?: never;
} & ButtonHTMLAttributes<HTMLButtonElement>;

type ButtonProps = LinkButtonProps | NativeButtonProps;

const variants = {
  primary:
    'border-console-accent bg-console-accent text-console-accent-foreground shadow-[0_0_24px_rgba(45,213,195,0.2)] hover:bg-console-accent/90',
  secondary:
    'border-console-border bg-console-panel text-console-foreground hover:border-console-accent/70 hover:text-console-accent',
  ghost:
    'border-transparent bg-transparent text-console-muted hover:border-console-border hover:text-console-foreground',
};

export function Button({ children, variant = 'primary', className = '', ...props }: ButtonProps) {
  const classes = [
    'inline-flex min-h-10 items-center justify-center gap-2 rounded-md border px-4 py-2 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-console-accent focus-visible:ring-offset-2 focus-visible:ring-offset-console-background',
    variants[variant],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  if ('href' in props && typeof props.href === 'string') {
    const { href, ...anchorProps } = props;

    return (
      <Link href={href} className={classes} {...anchorProps}>
        {children}
      </Link>
    );
  }

  return (
    <button className={classes} {...(props as ButtonHTMLAttributes<HTMLButtonElement>)}>
      {children}
    </button>
  );
}
