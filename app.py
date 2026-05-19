import streamlit as st
import pdfplumber
from deep_translator import GoogleTranslator
import io
import os
import urllib.request
from fpdf import FPDF

# Configuração da página - Mantendo centrado para focar no texto do livro
st.set_page_config(page_title="Leitor & Tradutor de Livros Pro", page_icon="📚", layout="centered")

# Estilização CSS para criar um ambiente de leitura confortável (Estilo Kindle)
st.markdown("""
    <style>
    .caixa-leitura {
        background-color: #fcfbf7; /* Tom levemente sépia */
        color: #1a1a1a;
        padding: 30px;
        border-radius: 8px;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.05);
        font-family: 'Georgia', serif;
        font-size: 18px;
        line-height: 1.8;
        margin-bottom: 25px;
        text-align: justify;
    }
    .titulo-pagina {
        font-family: 'Helvetica', sans-serif;
        color: #2c3e50;
        border-bottom: 2px solid #ecf0f1;
        padding-bottom: 8px;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📚 Tradutor & Leitor de Livros Pro")
st.write("Carregue seu livro, ajuste as páginas e baixe suas traduções em blocos de forma segura.")

# Garante o download de uma fonte TrueType robusta para evitar erros de caractere no Linux/Streamlit Cloud
@st.cache_data
def baixar_fonte_utf8():
    font_url = "https://github.com/reingart/pyfpdf/raw/master/fpdf/font/DejaVuSans.ttf"
    font_path = "DejaVuSans.ttf"
    if not os.path.exists(font_path):
        try:
            urllib.request.urlretrieve(font_url, font_path)
        except Exception:
            pass
    return font_path if os.path.exists(font_path) else None

caminho_fonte = baixar_fonte_utf8()

# Inicializando o Histórico de Downloads na memória do Streamlit se não existir
if 'blocos_salvos' not in st.session_state:
    st.session_state['blocos_salvos'] = []

# Barra lateral para configurações
st.sidebar.header("⚙️ Configurações")

idiomas_suportados = {
    "Português": "pt",
    "Inglês": "en",
    "Espanhol": "es",
    "Francês": "fr",
    "Alemão": "de",
    "Italiano": "it"
}

idioma_destino_nome = st.sidebar.selectbox("Traduzir o livro para:", list(idiomas_suportados.keys()))
codigo_destino = idiomas_suportados[idioma_destino_nome]

# Escolher a página inicial da tradução
pagina_inicio = st.sidebar.number_input("Começar a tradução a partir da página:", min_value=1, value=1, step=1)

uploaded_file = st.file_uploader("Selecione o arquivo PDF do livro", type=["pdf"])

# Função auxiliar atualizada para gerar PDF com suporte real e nativo a UTF-8
def gerar_pdf_bytes(lista_paginas):
    pdf_saida = FPDF()
    pdf_saida.set_auto_page_break(auto=True, margin=15)
    
    # Se a fonte TrueType foi baixada com sucesso, nós a registramos no sistema de PDF
    if caminho_fonte:
        pdf_saida.add_font("DejaVu", "", caminho_fonte, uni=True)
        nome_fonte = "DejaVu"
    else:
        nome_fonte = "Helvetica" # Fallback caso falhe o download
        
    for num_pag, texto_pag in lista_paginas:
        pdf_saida.add_page()
        
        # Cabeçalho da página
        if caminho_fonte:
            pdf_saida.set_font("DejaVu", "", 14)
        else:
            pdf_saida.set_font("Helvetica", "B", 14)
            
        pdf_saida.cell(0, 10, f"Página {num_pag}", ln=True, align="C")
        pdf_saida.ln(5)
        
        # Corpo do texto
        if caminho_fonte:
            pdf_saida.set_font("DejaVu", "", 10)
            # Unicode Real: Não precisa decodificar para latin-1! Enviamos a string limpa diretamente
            texto_final = texto_pag
        else:
            pdf_saida.set_font("Helvetica", "", 11)
            # Tratamento caso use a fonte padrão sem Unicode
            texto_final = texto_pag.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'").replace("—", "-")
            texto_final = texto_final.encode('latin-1', 'replace').decode('latin-1')
        
        pdf_saida.multi_cell(0, 6, texto_final)
        
    # Gera os bytes finais de maneira totalmente segura
    return pdf_saida.output(dest='S') if hasattr(pdf_saida, 'output') else pdf_saida.output()

# Se existirem blocos gerados anteriormente na sessão, mostra eles fixos na barra lateral
if st.session_state['blocos_salvos']:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 Blocos Parciais Disponíveis")
    for titulo, pdf_data, nome_arq in st.session_state['blocos_salvos']:
        st.sidebar.download_button(
            label=titulo,
            data=pdf_data,
            file_name=nome_arq,
            mime="application/pdf",
            key=f"sidebar_{titulo}"
        )

if uploaded_file is not None:
    st.success("Livro carregado com sucesso!")
    
    # Botão para limpar o histórico caso mude de livro
    if st.sidebar.button("🗑️ Limpar Downloads Parciais Antigos"):
        st.session_state['blocos_salvos'] = []
        st.rerun()
        
    if st.button("✨ Iniciar Tradução e Formatação"):
        try:
            translator = GoogleTranslator(source='auto', target=codigo_destino)
            
            paginas_traduzidas_total = []  
            bloco_atual = []               
            
            with pdfplumber.open(uploaded_file) as pdf:
                total_paginas = len(pdf.pages)
                
                if pagina_inicio > total_paginas:
                    st.error(f"Erro: O livro possui apenas {total_paginas} páginas.")
                else:
                    st.info(f"Traduzindo da página {pagina_inicio} até {total_paginas}...")
                    
                    progresso = st.progress(0)
                    st_status = st.empty()
                    
                    for i in range(pagina_inicio - 1, total_paginas):
                        pagina = pdf.pages[i]
                        num_real_pagina = i + 1
                        
                        st_status.text(f"📖 Processando página {num_real_pagina} de {total_paginas}...")
                        
                        texto_original = pagina.extract_text()
                        
                        if texto_original:
                            paragrafos = texto_original.split("\n")
                            texto_pagina_traduzida = ""
                            
                            for p in paragrafos:
                                if p.strip():
                                    try:
                                        traducao_linha = translator.translate(p)
                                        texto_pagina_traduzida += traducao_linha + "\n\n"
                                    except:
                                        texto_pagina_traduzida += p + "\n\n"
                            
                            # Mostra a leitura na tela em tempo real
                            st.markdown(f"<h3 class='titulo-pagina'>Página {num_real_pagina}</h3>", unsafe_allow_html=True)
                            aba_traduzida, aba_original = st.tabs(["✨ Texto Traduzido", "📄 Texto Original"])
                            
                            with aba_traduzida:
                                st.markdown(f"<div class='caixa-leitura'>{texto_pagina_traduzida}</div>", unsafe_allow_html=True)
                            with aba_original:
                                st.markdown(f"<div class='caixa-leitura' style='background-color: #f5f6fa;'>{texto_original}</div>", unsafe_allow_html=True)
                            
                            st.markdown("---")
                            
                            paginas_traduzidas_total.append((num_real_pagina, texto_pagina_traduzida))
                            bloco_atual.append((num_real_pagina, texto_pagina_traduzida))
                            
                            # --- SE COMPLETOU 50 PÁGINAS NO BLOCO ---
                            if len(bloco_atual) == 50:
                                p_inicial_bloco = bloco_atual[0][0]
                                p_final_bloco = bloco_atual[-1][0]
                                
                                # Gera o PDF do bloco atual usando a nova função com fontes TrueType
                                pdf_bloco_bytes = gerar_pdf_bytes(bloco_atual)
                                buffer_bloco = io.BytesIO(pdf_bloco_bytes)
                                
                                # Salva permanentemente na sessão
                                st.session_state['blocos_salvos'].append((
                                    f"📥 Baixar Págs {p_inicial_bloco}-{p_final_bloco}",
                                    buffer_bloco,
                                    f"bloco_paginas_{p_inicial_bloco}_a_{p_final_bloco}.pdf"
                                ))
                                
                                st.toast(f"💾 Bloco das páginas {p_inicial_bloco} a {p_final_bloco} salvo na barra lateral!", icon="💾")
                                
                                bloco_atual = []
                        
                        # Atualiza a barra de progresso
                        total_a_traduzir = total_paginas - (pagina_inicio - 1)
                        atual_traduzido = (i - (pagina_inicio - 1)) + 1
                        progresso.progress(atual_traduzido / total_a_traduzir)
                    
                    st_status.text("✨ Processamento concluído!")
                    
                    # Bloco final (sobras de páginas que não somaram 50 exatas)
                    if bloco_atual and len(paginas_traduzidas_total) > len(bloco_atual):
                        p_in = bloco_atual[0][0]
                        p_fi = bloco_atual[-1][0]
                        pdf_final_bytes = gerar_pdf_bytes(bloco_atual)
                        st.session_state['blocos_salvos'].append((
                            f"📥 Baixar Págs {p_in}-{p_fi} (Final)",
                            io.BytesIO(pdf_final_bytes),
                            f"bloco_final_{p_in}_a_{p_fi}.pdf"
                        ))
                    
                    # PDF do Livro Inteiro
                    pdf_total_bytes = gerar_pdf_bytes(paginas_traduzidas_total)
                    buffer_pdf = io.BytesIO(pdf_total_bytes)
                    
                    st.sidebar.markdown("---")
                    st.sidebar.success("Tradução Completa!")
                    st.sidebar.download_button(
                        label=f"📥 Baixar PDF Total Traduzido",
                        data=buffer_pdf,
                        file_name=f"livro_completo_desde_pag_{pagina_inicio}.pdf",
                        mime="application/pdf",
                        key="btn_completo_final"
                    )
                    
                    st.rerun()
                
        except Exception as e:
            st.error(f"Ocorreu um erro durante o processo: {e}")
