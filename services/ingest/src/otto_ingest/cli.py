from __future__ import annotations

import click

from otto_core.ingest_store import IngestEmAndamentoError, IngestParamsError, executar_coleta


@click.group()
def main() -> None:
    """OTTO — coleta e persistência PNCP."""


@main.command("ingest")
@click.option("--days", default=None, type=int, help="Janela de dias retroativos")
@click.option("--uf", default=None, help="UF (ex: PI)")
def ingest(days: int | None, uf: str | None) -> None:
    """Coleta publicações PNCP e grava no SQLite."""
    try:
        out = executar_coleta(days=days, uf=uf)
    except IngestEmAndamentoError as e:
        raise click.ClickException(str(e)) from e
    except IngestParamsError as e:
        raise click.ClickException(str(e)) from e
    except Exception as e:
        raise click.ClickException(f"Coleta falhou: {e}") from e

    click.echo(
        f"Coleta concluída: {out['total_bruto']} bruto | "
        f"{out['total_novos']} novos | {out['total_atualizados']} atualizados | "
        f"{out['erros']} erros"
    )


@main.command("alertas")
@click.option("--hours", default=24, type=int, help="Janela retroativa em horas")
@click.option("--uf", default="PI", help="UF")
@click.option("--confianca", default="alta", help="Confiança mínima (alta/baixa)")
def alertas(hours: int, uf: str, confianca: str) -> None:
    """Lista alertas V1: novas TI, mudanças e prazos urgentes."""
    from datetime import datetime, timedelta, timezone

    from otto_core.db import get_alertas, get_connection, init_db

    desde = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=max(1, hours))).isoformat()
    conn = get_connection()
    init_db(conn)
    try:
        data = get_alertas(conn, uf=uf.upper(), confianca=confianca, desde=desde)
    finally:
        conn.close()

    click.echo(f"Alertas OTTO · PI · confiança={confianca} · desde {desde[:16]}")
    click.echo(f"  Novas alta confiança: {data['novas_alta_confianca']}")
    click.echo(f"  Mudanças (7d):        {data['mudancas_7d']}")
    click.echo(f"  Vence em <=3 dias:     {data['vencendo_urgente_3d']}")
    if data["items"]:
        click.echo("")
        for item in data["items"]:
            org = item.get("orgao_razao_social", "")[:40]
            click.echo(f"  [{item['tipo']}] {org} — {item.get('numero_controle_pncp', '')}")
    else:
        click.echo("\n  Nenhum alerta no recorte.")


if __name__ == "__main__":
    main()
