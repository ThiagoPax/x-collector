"""Módulo de análise de conteúdo com OpenAI - Versão Completa."""
from __future__ import annotations
import os
import json
from typing import Optional, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class TopPost:
    """Representa um post de destaque."""
    def __init__(self, post, rank: int, criteria: str):
        self.rank = rank
        self.author = f"@{post.author_handle}"
        self.author_name = post.author_name
        self.text = post.text[:150] + "..." if len(post.text) > 150 else post.text
        self.url = post.url
        self.likes = post.metrics.likes or 0
        self.reposts = post.metrics.reposts or 0
        self.replies = post.metrics.replies or 0
        self.views = post.metrics.views or 0
        self.engagement_total = self.likes + self.reposts + self.replies
        self.criteria = criteria
    
    def to_text(self) -> str:
        """Retorna texto formatado do post."""
        lines = [
            f"  #{self.rank} - {self.author_name} ({self.author})",
            f"     📝 \"{self.text}\"",
            f"     ❤️ {self.likes:,} curtidas | 🔁 {self.reposts:,} reposts | 💬 {self.replies:,} respostas | 👁️ {self.views:,} views",
            f"     📊 Engajamento total: {self.engagement_total:,} interações",
            f"     🔗 {self.url}",
            f"     ✨ Critério de destaque: {self.criteria}",
        ]
        return "\n".join(lines).replace(",", ".")
    
    def to_html(self) -> str:
        """Retorna HTML formatado do post."""
        return f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #1DA1F2;">
            <strong>#{self.rank}</strong> - {self.author_name} (<span style="color: #1DA1F2;">{self.author}</span>)
            <p style="margin: 10px 0; font-style: italic;">"{self.text}"</p>
            <div style="display: flex; gap: 15px; flex-wrap: wrap; font-size: 14px;">
                <span>❤️ {self.likes:,} curtidas</span>
                <span>🔁 {self.reposts:,} reposts</span>
                <span>💬 {self.replies:,} respostas</span>
                <span>👁️ {self.views:,} views</span>
            </div>
            <p style="margin: 5px 0; font-weight: bold; color: #28a745;">📊 Engajamento total: {self.engagement_total:,} interações</p>
            <p style="margin: 5px 0; font-size: 12px; color: #666;">✨ Critério: {self.criteria}</p>
            <a href="{self.url}" style="color: #1DA1F2; font-size: 12px;">🔗 Ver post original</a>
        </div>
        """.replace(",", ".")


class DiagnosticReport:
    """Relatório de diagnóstico estruturado com Top 5 posts."""
    
    def __init__(self):
        self.valor_percebido: str = ""
        self.mensagem_principal: str = ""
        self.submensagens: List[str] = []
        self.possiveis_vieses: List[str] = []
        self.pontos_positivos: List[str] = []
        self.pontos_negativos: List[str] = []
        self.elementos_destaque: List[str] = []
        self.percepcao_qualidade: str = ""
        self.observacoes: List[str] = []
        self.resumo_metricas: dict = {}
        self.top_5_posts: List[TopPost] = []
        self.generated_at: datetime = datetime.now()
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "valor_percebido": self.valor_percebido,
            "mensagem_principal": self.mensagem_principal,
            "submensagens": self.submensagens,
            "possiveis_vieses": self.possiveis_vieses,
            "pontos_positivos": self.pontos_positivos,
            "pontos_negativos": self.pontos_negativos,
            "elementos_destaque": self.elementos_destaque,
            "percepcao_qualidade": self.percepcao_qualidade,
            "observacoes": self.observacoes,
            "resumo_metricas": self.resumo_metricas,
            "top_5_posts": [vars(p) for p in self.top_5_posts],
            "generated_at": self.generated_at.isoformat(),
        }
    
    def to_text(self) -> str:
        """Converte para texto formatado."""
        lines = []
        lines.append("=" * 70)
        lines.append("📊 RELATÓRIO DE DIAGNÓSTICO DO RESULTADO")
        lines.append("=" * 70)
        lines.append("")
        
        # Métricas resumidas
        if self.resumo_metricas:
            lines.append("📈 RESUMO DE MÉTRICAS")
            lines.append("-" * 50)
            for key, value in self.resumo_metricas.items():
                lines.append(f"  • {key}: {value}")
            lines.append("")
        
        # TOP 5 POSTS COM MAIOR ENGAJAMENTO
        if self.top_5_posts:
            lines.append("🏆 TOP 5 POSTS COM MAIOR ENGAJAMENTO")
            lines.append("-" * 50)
            lines.append("")
            for post in self.top_5_posts:
                lines.append(post.to_text())
                lines.append("")
            lines.append("")
        
        # Valor percebido
        lines.append("💎 VALOR PERCEBIDO PELO PÚBLICO FINAL")
        lines.append("-" * 50)
        lines.append(f"  {self.valor_percebido}")
        lines.append("")
        
        # Mensagem principal
        lines.append("📌 MENSAGEM PRINCIPAL IDENTIFICADA")
        lines.append("-" * 50)
        lines.append(f"  {self.mensagem_principal}")
        lines.append("")
        
        # Submensagens
        if self.submensagens:
            lines.append("📝 SUBMENSAGENS IMPLÍCITAS")
            lines.append("-" * 50)
            for msg in self.submensagens:
                lines.append(f"  • {msg}")
            lines.append("")
        
        # Possíveis vieses
        if self.possiveis_vieses:
            lines.append("⚠️ POSSÍVEIS VIESES IDENTIFICADOS")
            lines.append("-" * 50)
            for vies in self.possiveis_vieses:
                lines.append(f"  • {vies}")
            lines.append("")
        
        # Pontos positivos
        if self.pontos_positivos:
            lines.append("✅ PONTOS POSITIVOS")
            lines.append("-" * 50)
            for ponto in self.pontos_positivos:
                lines.append(f"  • {ponto}")
            lines.append("")
        
        # Pontos negativos
        if self.pontos_negativos:
            lines.append("❌ PONTOS NEGATIVOS / LIMITAÇÕES")
            lines.append("-" * 50)
            for ponto in self.pontos_negativos:
                lines.append(f"  • {ponto}")
            lines.append("")
        
        # Elementos de destaque (além do Top 5)
        if self.elementos_destaque:
            lines.append("🌟 OUTROS ELEMENTOS DE DESTAQUE")
            lines.append("-" * 50)
            for elem in self.elementos_destaque:
                lines.append(f"  • {elem}")
            lines.append("")
        
        # Percepção de qualidade
        lines.append("📊 PERCEPÇÃO GERAL DA QUALIDADE")
        lines.append("-" * 50)
        lines.append(f"  {self.percepcao_qualidade}")
        lines.append("")
        
        # Observações
        if self.observacoes:
            lines.append("💡 OBSERVAÇÕES PARA TOMADA DE DECISÃO")
            lines.append("-" * 50)
            for obs in self.observacoes:
                lines.append(f"  • {obs}")
            lines.append("")
        
        lines.append("=" * 70)
        lines.append(f"Relatório gerado em: {self.generated_at.strftime('%d/%m/%Y às %H:%M')}")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def to_html(self) -> str:
        """Converte para HTML formatado."""
        html = """
        <div style="font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto;">
            <h2 style="color: #1DA1F2; border-bottom: 2px solid #1DA1F2; padding-bottom: 10px;">
                📊 Relatório de Diagnóstico do Resultado
            </h2>
        """
        
        # Métricas
        if self.resumo_metricas:
            html += """
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; margin: 20px 0;">
                <h3 style="margin-top: 0;">📈 Resumo de Métricas</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
            """
            for key, value in self.resumo_metricas.items():
                html += f"""
                <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold;">{value}</div>
                    <div style="font-size: 12px; opacity: 0.9;">{key}</div>
                </div>
                """
            html += "</div></div>"
        
        # TOP 5 POSTS
        if self.top_5_posts:
            html += """
            <div style="background: #fff3cd; padding: 20px; border-radius: 12px; margin: 20px 0; border: 2px solid #ffc107;">
                <h3 style="margin-top: 0; color: #856404;">🏆 TOP 5 POSTS COM MAIOR ENGAJAMENTO</h3>
            """
            for post in self.top_5_posts:
                html += post.to_html()
            html += "</div>"
        
        # Seções principais
        sections = [
            ("💎 Valor Percebido pelo Público Final", self.valor_percebido, "#e8f5e9"),
            ("📌 Mensagem Principal Identificada", self.mensagem_principal, "#fff3e0"),
        ]
        
        for title, content, bg_color in sections:
            if content:
                html += f"""
                <div style="background: {bg_color}; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <h3 style="margin-top: 0;">{title}</h3>
                    <p>{content}</p>
                </div>
                """
        
        # Listas
        list_sections = [
            ("📝 Submensagens Implícitas", self.submensagens, "#f3e5f5"),
            ("⚠️ Possíveis Vieses", self.possiveis_vieses, "#ffebee"),
            ("✅ Pontos Positivos", self.pontos_positivos, "#e8f5e9"),
            ("❌ Pontos Negativos", self.pontos_negativos, "#ffebee"),
            ("🌟 Outros Elementos de Destaque", self.elementos_destaque, "#fff8e1"),
        ]
        
        for title, items, bg_color in list_sections:
            if items:
                html += f"""
                <div style="background: {bg_color}; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <h3 style="margin-top: 0;">{title}</h3>
                    <ul>
                """
                for item in items:
                    html += f"<li>{item}</li>"
                html += "</ul></div>"
        
        # Percepção de qualidade
        if self.percepcao_qualidade:
            html += f"""
            <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h3 style="margin-top: 0;">📊 Percepção Geral da Qualidade</h3>
                <p>{self.percepcao_qualidade}</p>
            </div>
            """
        
        # Observações
        if self.observacoes:
            html += """
            <div style="background: #fffde7; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #ffc107;">
                <h3 style="margin-top: 0;">💡 Observações para Tomada de Decisão</h3>
                <ul>
            """
            for obs in self.observacoes:
                html += f"<li>{obs}</li>"
            html += "</ul></div>"
        
        html += f"""
            <p style="color: #666; font-size: 12px; text-align: center; margin-top: 20px;">
                Relatório gerado em: {self.generated_at.strftime('%d/%m/%Y às %H:%M')}
            </p>
        </div>
        """
        
        return html


class ContentAnalyzer:
    """Analisador de conteúdo usando OpenAI."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
    
    def is_configured(self) -> bool:
        """Verifica se a API key está configurada."""
        return bool(self.api_key and self.api_key.startswith("sk-"))
    
    def _calculate_top_5_posts(self, posts: list) -> List[TopPost]:
        """Calcula os Top 5 posts com maior engajamento."""
        if not posts:
            return []
        
        # Calcular engajamento total para cada post
        posts_with_engagement = []
        for p in posts:
            engagement = (p.metrics.likes or 0) + (p.metrics.reposts or 0) + (p.metrics.replies or 0)
            posts_with_engagement.append((p, engagement))
        
        # Ordenar por engajamento total (decrescente)
        sorted_posts = sorted(posts_with_engagement, key=lambda x: x[1], reverse=True)
        
        top_5 = []
        for i, (post, engagement) in enumerate(sorted_posts[:5], 1):
            # Determinar critério principal de destaque
            likes = post.metrics.likes or 0
            reposts = post.metrics.reposts or 0
            replies = post.metrics.replies or 0
            views = post.metrics.views or 0
            
            criteria_parts = []
            if likes > 0:
                criteria_parts.append(f"{likes:,} curtidas".replace(",", "."))
            if reposts > 0:
                criteria_parts.append(f"{reposts:,} reposts".replace(",", "."))
            if replies > 0:
                criteria_parts.append(f"{replies:,} respostas".replace(",", "."))
            if views > 0:
                criteria_parts.append(f"{views:,} views".replace(",", "."))
            
            criteria = f"Engajamento total: {engagement:,} ({', '.join(criteria_parts)})".replace(",", ".")
            
            top_5.append(TopPost(post, i, criteria))
        
        return top_5
    
    async def analyze_posts(self, posts: list, query: str) -> DiagnosticReport:
        """
        Analisa uma lista de posts e gera relatório diagnóstico.
        
        Args:
            posts: Lista de posts (objetos Post)
            query: Query/pesquisa utilizada
            
        Returns:
            DiagnosticReport com a análise
        """
        report = DiagnosticReport()
        
        # Calcular métricas básicas
        total_posts = len(posts)
        total_likes = sum(p.metrics.likes or 0 for p in posts)
        total_reposts = sum(p.metrics.reposts or 0 for p in posts)
        total_views = sum(p.metrics.views or 0 for p in posts)
        total_replies = sum(p.metrics.replies or 0 for p in posts)
        total_engagement = total_likes + total_reposts + total_replies
        
        # Formatar números com ponto como separador de milhar
        def fmt(n):
            return f"{n:,}".replace(",", ".")
        
        report.resumo_metricas = {
            "Total de posts": fmt(total_posts),
            "Total de curtidas": fmt(total_likes),
            "Total de reposts": fmt(total_reposts),
            "Total de respostas": fmt(total_replies),
            "👁️ TOTAL DE VISUALIZAÇÕES": fmt(total_views),
            "Engajamento total": fmt(total_engagement),
            "Média de curtidas/post": f"{total_likes/max(total_posts,1):.1f}",
            "Média de views/post": f"{total_views/max(total_posts,1):.1f}",
        }
        
        # Calcular Top 5 posts
        report.top_5_posts = self._calculate_top_5_posts(posts)
        
        # Se não tem API key, gerar relatório básico
        if not self.is_configured():
            return self._generate_basic_report(posts, query, report)
        
        # Usar OpenAI para análise avançada
        try:
            return await self._analyze_with_openai(posts, query, report)
        except Exception as e:
            print(f"⚠️ Erro na análise OpenAI: {e}. Gerando relatório básico.")
            return self._generate_basic_report(posts, query, report)
    
    def _generate_basic_report(self, posts: list, query: str, report: DiagnosticReport) -> DiagnosticReport:
        """Gera relatório básico sem IA."""
        total_posts = len(posts)
        total_views = sum(p.metrics.views or 0 for p in posts)
        total_likes = sum(p.metrics.likes or 0 for p in posts)
        
        # Análise básica por frequência de palavras e métricas
        all_hashtags = []
        all_mentions = []
        
        for p in posts:
            all_hashtags.extend(p.hashtags)
            all_mentions.extend(p.mentions)
        
        # Contagem de hashtags
        hashtag_counts = {}
        for h in all_hashtags:
            hashtag_counts[h] = hashtag_counts.get(h, 0) + 1
        top_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Contagem de mentions
        mention_counts = {}
        for m in all_mentions:
            mention_counts[m] = mention_counts.get(m, 0) + 1
        top_mentions = sorted(mention_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Preencher relatório
        report.valor_percebido = f"Conteúdo relacionado a '{query}' com {total_posts:,} publicações coletadas e {total_views:,} visualizações totais, demonstrando interesse e discussão ativa sobre o tema.".replace(",", ".")
        
        report.mensagem_principal = f"O tema '{query}' gera discussão significativa na plataforma X, acumulando {total_likes:,} curtidas em {total_posts:,} posts analisados.".replace(",", ".")
        
        report.submensagens = []
        if top_hashtags:
            report.submensagens.append(f"Hashtags mais usadas: {', '.join(h[0] for h in top_hashtags)}")
        if top_mentions:
            report.submensagens.append(f"Perfis mais mencionados: {', '.join(m[0] for m in top_mentions)}")
        
        report.possiveis_vieses = [
            "A coleta pode refletir o algoritmo do X que prioriza certos conteúdos",
            "Posts mais recentes podem ter menos engajamento por tempo de exposição",
            f"Amostra de {total_posts:,} posts pode não representar todo o universo de discussões".replace(",", "."),
        ]
        
        # Análise de engajamento
        total_engagement = sum((p.metrics.likes or 0) + (p.metrics.reposts or 0) for p in posts)
        avg_engagement = total_engagement / max(total_posts, 1)
        
        report.pontos_positivos = []
        if avg_engagement > 100:
            report.pontos_positivos.append(f"Alto engajamento médio: {avg_engagement:.0f} interações/post")
        elif avg_engagement > 10:
            report.pontos_positivos.append(f"Engajamento moderado: {avg_engagement:.0f} interações/post")
        
        report.pontos_positivos.append(f"{total_posts:,} posts coletados com sucesso".replace(",", "."))
        report.pontos_positivos.append(f"{total_views:,} visualizações totais alcançadas".replace(",", "."))
        
        if report.top_5_posts:
            top = report.top_5_posts[0]
            report.pontos_positivos.append(f"Post mais engajado: {top.author} com {top.engagement_total:,} interações".replace(",", "."))
        
        report.pontos_negativos = [
            "Análise sem IA - insights limitados à estatística básica",
            "Para análise semântica avançada, configure OPENAI_API_KEY no .env",
        ]
        
        report.percepcao_qualidade = f"Dataset de {total_posts:,} posts coletados com {total_views:,} views totais. O Top 5 de posts mais engajados está destacado acima. Qualidade dos dados: adequada para análise quantitativa.".replace(",", ".")
        
        report.observacoes = [
            "Os Top 5 posts foram selecionados pelo critério de engajamento total (curtidas + reposts + respostas)",
            f"O alcance total de {total_views:,} views indica visibilidade significativa do tema".replace(",", "."),
            "Considere filtros adicionais para refinar a amostra se necessário",
        ]
        
        return report
    
    async def _analyze_with_openai(self, posts: list, query: str, report: DiagnosticReport) -> DiagnosticReport:
        """Analisa posts usando a API da OpenAI."""
        import httpx
        
        # Preparar amostra de posts (máximo 50 para contexto melhor)
        sample_posts = posts[:50]
        
        # Calcular totais
        total_views = sum(p.metrics.views or 0 for p in posts)
        total_likes = sum(p.metrics.likes or 0 for p in posts)
        total_reposts = sum(p.metrics.reposts or 0 for p in posts)
        
        posts_text = "\n\n".join([
            f"Post {i+1} (@{p.author_handle}):\n"
            f"Texto: {p.text}\n"
            f"Likes: {p.metrics.likes or 0} | Reposts: {p.metrics.reposts or 0} | Views: {p.metrics.views or 0}"
            for i, p in enumerate(sample_posts)
        ])
        
        # Top 5 já calculados
        top5_text = "\n".join([
            f"#{i+1}: @{p.author} - {p.likes} curtidas, {p.reposts} reposts, {p.views} views"
            for i, p in enumerate(report.top_5_posts)
        ])
        
        prompt = f"""Analise os seguintes posts do X (Twitter) coletados com a pesquisa "{query}" e gere um relatório diagnóstico estruturado.

MÉTRICAS GERAIS (TODOS OS {len(posts)} POSTS):
- Total de posts: {len(posts):,}
- Total de curtidas: {total_likes:,}
- Total de reposts: {total_reposts:,}
- TOTAL DE VISUALIZAÇÕES: {total_views:,}

TOP 5 POSTS MAIS ENGAJADOS:
{top5_text}

AMOSTRA DE POSTS (primeiros {len(sample_posts)}):
{posts_text}

Gere um JSON com a seguinte estrutura (responda APENAS com o JSON, sem markdown):
{{
    "valor_percebido": "Descrição do valor que este conteúdo oferece ao público final, mencionando o alcance de {total_views:,} visualizações",
    "mensagem_principal": "A mensagem central identificada nos posts",
    "submensagens": ["submensagem 1", "submensagem 2", "submensagem 3"],
    "possiveis_vieses": ["viés 1", "viés 2"],
    "pontos_positivos": ["ponto positivo 1 incluindo métricas", "ponto positivo 2", "ponto positivo 3"],
    "pontos_negativos": ["limitação 1", "limitação 2"],
    "elementos_destaque": ["insight sobre o top 5 de posts", "tendência identificada"],
    "percepcao_qualidade": "Avaliação geral incluindo o alcance de {total_views:,} views",
    "observacoes": ["recomendação 1 baseada nos dados", "recomendação 2"]
}}"""

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "Você é um analista de mídias sociais especializado em análise de conteúdo do X/Twitter. Responda apenas em português brasileiro. Sempre mencione métricas concretas como visualizações totais, curtidas e engajamento."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2500,
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Limpar possíveis marcadores de código
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            # Parse do JSON
            analysis = json.loads(content)
            
            # Preencher relatório (mantendo Top 5 já calculado)
            report.valor_percebido = analysis.get("valor_percebido", "")
            report.mensagem_principal = analysis.get("mensagem_principal", "")
            report.submensagens = analysis.get("submensagens", [])
            report.possiveis_vieses = analysis.get("possiveis_vieses", [])
            report.pontos_positivos = analysis.get("pontos_positivos", [])
            report.pontos_negativos = analysis.get("pontos_negativos", [])
            report.elementos_destaque = analysis.get("elementos_destaque", [])
            report.percepcao_qualidade = analysis.get("percepcao_qualidade", "")
            report.observacoes = analysis.get("observacoes", [])
            
            return report


async def generate_diagnostic_report(posts: list, query: str, api_key: Optional[str] = None) -> DiagnosticReport:
    """
    Função de conveniência para gerar relatório diagnóstico.
    
    Args:
        posts: Lista de posts
        query: Query utilizada na coleta
        api_key: Chave da OpenAI (opcional, usa .env se não fornecida)
        
    Returns:
        DiagnosticReport
    """
    analyzer = ContentAnalyzer(api_key)
    return await analyzer.analyze_posts(posts, query)
