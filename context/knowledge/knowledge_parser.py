#!/usr/bin/env python3
"""
Knowledge Parser for PagBank - Converts raw knowledge.md to structured CSV format
Agent B: Knowledge Base Development
"""

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class KnowledgeEntry:
    """Structured knowledge entry following PagBank schema"""
    conteudo: str
    area: str
    tipo_produto: str
    tipo_informacao: str
    nivel_complexidade: str
    publico_alvo: str
    palavras_chave: str
    atualizado_em: str


class PagBankKnowledgeParser:
    """Parser for PagBank knowledge from raw markdown to structured CSV"""
    
    # Product type mapping by area
    PRODUCT_TYPES = {
        'cartoes': [
            'cartao_credito', 'cartao_debito', 'cartao_prepago', 
            'cartao_virtual', 'limite_credito'
        ],
        'conta_digital': [
            'conta_rendeira', 'pix', 'ted', 'doc', 'pagamento_contas', 
            'recarga_celular', 'recarga_servicos', 'portabilidade'
        ],
        'investimentos': [
            'cdb', 'lci', 'lca', 'renda_variavel', 'tesouro_direto', 
            'cofrinho', 'fundos'
        ],
        'credito': [
            'fgts', 'consignado_inss', 'consignado_publico', 
            'emprestimo_pessoal'
        ],
        'seguros': [
            'seguro_vida', 'seguro_residencia', 'seguro_conta', 
            'saude', 'seguro_cartao'
        ]
    }
    
    # Information type patterns
    INFO_PATTERNS = {
        'como_solicitar': [
            'como solicitar', 'como pedir', 'como fazer', 'passo a passo',
            'cadastrar', 'contratar', 'abrir conta', 'como funciona'
        ],
        'taxas': [
            'taxa', 'custo', 'valor', 'preço', 'tarifa', 'grátis',
            'gratuito', 'sem custo', 'mensalidade'
        ],
        'beneficios': [
            'vantagem', 'benefício', 'dinheiro de volta', 'cashback',
            'render', 'rendimento', 'lucro', 'ganho'
        ],
        'requisitos': [
            'requisito', 'condição', 'exigência', 'necessário',
            'obrigatório', 'documento', 'verificação'
        ],
        'prazos': [
            'prazo', 'tempo', 'dias úteis', 'imediato', 'instantâneo',
            'em até', 'minutos', 'horas'
        ],
        'limites': [
            'limite', 'máximo', 'mínimo', 'valor máximo', 'valor mínimo',
            'até', 'partir de'
        ],
        'problemas_comuns': [
            'problema', 'erro', 'dúvida', 'não consigo', 'falha',
            'solução', 'resolver', 'ajuda'
        ]
    }
    
    # Keywords for area detection
    AREA_KEYWORDS = {
        'cartoes': [
            'cartão', 'cartao', 'crédito', 'débito', 'prepago',
            'limite', 'anuidade', 'fatura', 'parcelado'
        ],
        'conta_digital': [
            'conta', 'pix', 'ted', 'transferência', 'pagamento',
            'recarga', 'celular', 'portabilidade', 'saldo'
        ],
        'investimentos': [
            'cdb', 'lci', 'lca', 'investir', 'render', 'cdi',
            'cofrinho', 'fundos', 'tesouro', 'aplicação'
        ],
        'credito': [
            'fgts', 'consignado', 'empréstimo', 'crédito', 'antecipação',
            'saque', 'aniversário', 'inss', 'taxa'
        ],
        'seguros': [
            'seguro', 'vida', 'residência', 'saúde', 'proteção',
            'cobertura', 'assistência', 'sinistro', 'invalidez'
        ]
    }
    
    def __init__(self, knowledge_file: Path):
        """Initialize parser with knowledge file"""
        self.knowledge_file = knowledge_file
        self.entries: List[KnowledgeEntry] = []
        
    def parse_knowledge(self) -> List[KnowledgeEntry]:
        """Parse the knowledge file and extract structured entries"""
        print(f"Parsing knowledge from: {self.knowledge_file}")
        
        # Read the entire file
        with open(self.knowledge_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into sections by headers
        sections = self._split_into_sections(content)
        
        # Process each section
        for section in sections:
            entries = self._process_section(section)
            self.entries.extend(entries)
        
        print(f"Extracted {len(self.entries)} knowledge entries")
        return self.entries
    
    def _split_into_sections(self, content: str) -> List[str]:
        """Split content into logical sections"""
        # Split by major headers (# or ##)
        sections = re.split(r'\n(?=#+\s)', content)
        
        # Filter out empty sections
        sections = [s.strip() for s in sections if s.strip()]
        
        return sections
    
    def _process_section(self, section: str) -> List[KnowledgeEntry]:
        """Process a section and extract knowledge entries"""
        entries = []
        
        # Extract title
        title_match = re.match(r'^#+\s*(.+)$', section, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "Informação PagBank"
        
        # Clean title
        title = re.sub(r'[*#]', '', title).strip()
        
        # Detect area from title and content
        area = self._detect_area(title, section)
        
        # Split section into paragraphs
        paragraphs = self._extract_paragraphs(section)
        
        # Process each meaningful paragraph
        for paragraph in paragraphs:
            if len(paragraph) > 50:  # Filter out very short paragraphs
                entry = self._create_entry(paragraph, area, title)
                if entry:
                    entries.append(entry)
        
        # Also create an entry for the main title/section
        if len(section) > 100:
            main_entry = self._create_entry(section[:500], area, title)
            if main_entry:
                entries.append(main_entry)
        
        return entries
    
    def _extract_paragraphs(self, section: str) -> List[str]:
        """Extract meaningful paragraphs from section"""
        paragraphs = []
        
        # Remove markdown formatting
        clean_section = re.sub(r'!\[.*?\]\(.*?\)', '', section)  # Remove images
        clean_section = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_section)  # Convert links
        clean_section = re.sub(r'[#*]+', '', clean_section)  # Remove markdown
        
        # Split by double newlines
        raw_paragraphs = re.split(r'\n\s*\n', clean_section)
        
        for paragraph in raw_paragraphs:
            # Clean up paragraph
            paragraph = re.sub(r'\s+', ' ', paragraph).strip()
            
            # Filter out unwanted content
            if (paragraph and 
                len(paragraph) > 30 and
                not paragraph.startswith('http') and
                not paragraph.startswith('Download') and
                not paragraph.startswith('Utilizamos cookies') and
                'Base64-Image-Removed' not in paragraph):
                paragraphs.append(paragraph)
        
        return paragraphs
    
    def _detect_area(self, title: str, content: str) -> str:
        """Detect the area based on title and content"""
        text = (title + " " + content).lower()
        
        # Count keyword matches for each area
        scores = {}
        for area, keywords in self.AREA_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[area] = score
        
        # Return area with highest score
        if scores:
            return max(scores, key=scores.get)
        
        return 'conta_digital'  # Default fallback
    
    def _detect_product_type(self, content: str, area: str) -> str:
        """Detect specific product type within area"""
        content_lower = content.lower()
        
        # Check for product-specific keywords
        for product_type in self.PRODUCT_TYPES.get(area, []):
            product_keywords = product_type.replace('_', ' ').split()
            if any(keyword in content_lower for keyword in product_keywords):
                return product_type
        
        # Return first product type for area as fallback
        products = self.PRODUCT_TYPES.get(area, ['geral'])
        return products[0]
    
    def _detect_info_type(self, content: str) -> str:
        """Detect information type from content"""
        content_lower = content.lower()
        
        # Count matches for each info type
        scores = {}
        for info_type, patterns in self.INFO_PATTERNS.items():
            score = sum(1 for pattern in patterns if pattern in content_lower)
            scores[info_type] = score
        
        # Return info type with highest score
        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return 'beneficios'  # Default fallback
    
    def _detect_complexity(self, content: str) -> str:
        """Detect complexity level from content"""
        content_lower = content.lower()
        
        # Advanced indicators
        advanced_indicators = [
            'configuração', 'personalizar', 'avançado', 'complexo',
            'análise', 'compliance', 'regulamentação', 'especialista'
        ]
        
        # Basic indicators
        basic_indicators = [
            'simples', 'fácil', 'básico', 'grátis', 'gratuito',
            'direto', 'rápido', 'início', 'começar'
        ]
        
        if any(indicator in content_lower for indicator in advanced_indicators):
            return 'avancado'
        elif any(indicator in content_lower for indicator in basic_indicators):
            return 'basico'
        
        return 'intermediario'  # Default
    
    def _detect_target_audience(self, content: str) -> str:
        """Detect target audience from content"""
        content_lower = content.lower()
        
        # Check for specific audience indicators
        if any(word in content_lower for word in ['cnpj', 'empresa', 'negócio', 'comercial']):
            return 'pessoa_juridica'
        elif any(word in content_lower for word in ['aposentado', 'pensionista', 'inss']):
            return 'aposentado'
        elif any(word in content_lower for word in ['menor', 'criança', 'adolescente', 'filho']):
            return 'menor_idade'
        elif any(word in content_lower for word in ['clt', 'trabalhador', 'salário']):
            return 'trabalhador_clt'
        
        return 'pessoa_fisica'  # Default
    
    def _extract_keywords(self, content: str) -> str:
        """Extract relevant keywords from content"""
        content_lower = content.lower()
        
        # Common words to exclude
        stop_words = {
            'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'da', 'do', 'das', 'dos',
            'e', 'ou', 'mas', 'por', 'para', 'com', 'sem', 'em', 'no', 'na',
            'você', 'seu', 'sua', 'seus', 'suas', 'que', 'como', 'quando', 'onde'
        }
        
        # Extract words
        words = re.findall(r'\b[a-záàâãéèêíìîóòôõúùûç]+\b', content_lower)
        
        # Filter and count
        word_counts = {}
        for word in words:
            if len(word) > 3 and word not in stop_words:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Get top keywords
        top_keywords = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:15]
        
        return ' '.join([word for word, count in top_keywords])
    
    def _create_entry(self, content: str, area: str, title: str) -> Optional[KnowledgeEntry]:
        """Create a knowledge entry from content"""
        # Clean content
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Skip if content is too short
        if len(content) < 50:
            return None
        
        # Extract structured data
        product_type = self._detect_product_type(content, area)
        info_type = self._detect_info_type(content)
        complexity = self._detect_complexity(content)
        target_audience = self._detect_target_audience(content)
        keywords = self._extract_keywords(content)
        
        # Create entry
        entry = KnowledgeEntry(
            conteudo=content[:1000],  # Limit content length
            area=area,
            tipo_produto=product_type,
            tipo_informacao=info_type,
            nivel_complexidade=complexity,
            publico_alvo=target_audience,
            palavras_chave=keywords,
            atualizado_em="2024-01"
        )
        
        return entry
    
    def save_to_csv(self, output_path: Path) -> None:
        """Save entries to CSV file"""
        print(f"Saving {len(self.entries)} entries to: {output_path}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'conteudo', 'area', 'tipo_produto', 'tipo_informacao',
                'nivel_complexidade', 'publico_alvo', 'palavras_chave', 'atualizado_em'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in self.entries:
                writer.writerow({
                    'conteudo': entry.conteudo,
                    'area': entry.area,
                    'tipo_produto': entry.tipo_produto,
                    'tipo_informacao': entry.tipo_informacao,
                    'nivel_complexidade': entry.nivel_complexidade,
                    'publico_alvo': entry.publico_alvo,
                    'palavras_chave': entry.palavras_chave,
                    'atualizado_em': entry.atualizado_em
                })
    
    def generate_statistics(self) -> Dict[str, Any]:
        """Generate statistics about the knowledge base"""
        if not self.entries:
            return {}
        
        stats = {
            'total_entries': len(self.entries),
            'by_area': {},
            'by_product_type': {},
            'by_info_type': {},
            'by_complexity': {},
            'by_target_audience': {}
        }
        
        # Count by category
        for entry in self.entries:
            stats['by_area'][entry.area] = stats['by_area'].get(entry.area, 0) + 1
            stats['by_product_type'][entry.tipo_produto] = stats['by_product_type'].get(entry.tipo_produto, 0) + 1
            stats['by_info_type'][entry.tipo_informacao] = stats['by_info_type'].get(entry.tipo_informacao, 0) + 1
            stats['by_complexity'][entry.nivel_complexidade] = stats['by_complexity'].get(entry.nivel_complexidade, 0) + 1
            stats['by_target_audience'][entry.publico_alvo] = stats['by_target_audience'].get(entry.publico_alvo, 0) + 1
        
        return stats


if __name__ == '__main__':
    # Initialize parser
    knowledge_file = Path(__file__).parent.parent / 'knowledge.md'
    parser = PagBankKnowledgeParser(knowledge_file)
    
    # Parse knowledge
    entries = parser.parse_knowledge()
    
    # Save to CSV
    output_path = Path(__file__).parent / 'pagbank_knowledge.csv'
    parser.save_to_csv(output_path)
    
    # Generate statistics
    stats = parser.generate_statistics()
    print("\nKnowledge Base Statistics:")
    print(f"Total entries: {stats['total_entries']}")
    print(f"By area: {stats['by_area']}")
    print(f"By complexity: {stats['by_complexity']}")
    print(f"By target audience: {stats['by_target_audience']}")