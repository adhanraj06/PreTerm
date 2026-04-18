import type { PropsWithChildren, ReactNode } from "react";

type AuthCardProps = PropsWithChildren<{
  eyebrow: string;
  title: string;
  subtitle: string;
  footer?: ReactNode;
}>;

export function AuthCard({ eyebrow, title, subtitle, footer, children }: AuthCardProps) {
  return (
    <section className="auth-card">
      <span className="eyebrow">{eyebrow}</span>
      <h1>{title}</h1>
      <p className="auth-card-subtitle">{subtitle}</p>
      {children}
      {footer ? <div className="auth-card-footer">{footer}</div> : null}
    </section>
  );
}
