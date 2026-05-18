import streamlit as st
import pdfplumber
from deep_translator import GoogleTranslator
import io

# Configuração da página - Mantendo centrado para focar no texto do livro
st.set_page_config(page_title="Leitor & Tradutor de Livros", page_icon="📚", layout="centered")

# Estilização CSS para criar um ambiente de leitura confortável (Estilo Kindle/E-book)
st.markdown("""
    <style>
    .caixa-leitura {
        background-color: #fcfbf7; /* Tom levemente sépia para não cansar os olhos */
        color: #1a1a1a;
        padding: 30px;
        border-radius: 8px;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.05);
        font-family: 'Georgia', serif; /* Fonte clássica de livros */
        font-size: 18px;
        line-height: 1.8; /* Excelente espaçamento entre linhas */
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

st.title("📚 Tradutor & Leitor de Livros")
st.write("Carregue seu livro, ajuste o idioma e leia confortavelmente diretamente pela tela.")

# Barra lateral para configurações
st.sidebar.header("Configurações")

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

uploaded_file = st.file_uploader("Selecione o arquivo PDF do livro", type=["pdf"])

if uploaded_file is not None:
    st.success("Livro carregado com sucesso!")
    
    if st.button("✨ Iniciar Tradução e Formatação"):
        try:
            translator = GoogleTranslator(source='auto', target=codigo_destino)
            texto_traduzido_completo = ""
            
            with pdfplumber.open(uploaded_file) as pdf:
                total_paginas = len(pdf.pages)
                
                progresso = st.progress(0)
                status_text = st.empty()
                
                for i, pagina in enumerate(pdf.pages):
                    status_text.text(f"📖 Processando e formatando página {i+1} de {total_paginas}...")
                    
                    texto_original = pagina.extract_text()
                    
                    if texto_original:
                        # Processando parágrafos
                        paragrafos = texto_original.split("\n")
                        texto_pagina_traduzida = ""
                        
                        for p in paragrafos:
                            if p.strip():
                                try:
                                    traducao_linha = translator.translate(p)
                                    texto_pagina_traduzida += traducao_linha + "\n\n" # Garante espaçamento entre parágrafos
                                except:
                                    texto_pagina_traduzida += p + "\n\n"
                        
                        # Interface de leitura organizada por abas para não poluir a tela
                        st.markdown(f"<h3 class='titulo-pagina'>Página {i+1}</h3>", unsafe_allow_html=True)
                        
                        aba_traduzida, aba_original = st.tabs(["✨ Texto Traduzido", "📄 Texto Original"])
                        
                        with aba_traduzida:
                            # Renderiza o texto dentro do container estilizado de e-book
                            st.markdown(f"<div class='caixa-leitura'>{texto_pagina_traduzida}</div>", unsafe_allow_html=True)
                        
                        with aba_original:
                            st.markdown(f"<div class='caixa-leitura' style='background-color: #f5f6fa;'>{texto_original}</div>", unsafe_allow_html=True)
                        
                        texto_traduzido_completo += f"--- PÁGINA {i+1} ---\n\n{texto_pagina_traduzida}\n\n"
                    
                    progresso.progress((i + 1) / total_paginas)
                
                status_text.text("✨ Livro totalmente processado!")
                
                # Preparando download
                buffer = io.BytesIO()
                buffer.write(texto_traduzido_completo.encode("utf-8"))
                buffer.seek(0)
                
                st.sidebar.markdown("---")
                st.sidebar.success("Tradução Concluída!")
                st.sidebar.download_button(
                    label=f"📥 Baixar Livro Completo ({idioma_destino_nome})",
                    data=buffer,
                    file_name=f"livro_traduzido_{codigo_destino}.txt",
                    mime="text/plain"
                )
                
        except Exception as e:
            st.error(f"Ocorreu um erro durante o processo: {e}")
