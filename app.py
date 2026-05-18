import streamlit as st
import pdfplumber
from deep_translator import GoogleTranslator
import io
from fpdf import FPDF

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
    .aviso-bloco {
        background-color: #e8f4fd;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #2196f3;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📚 Tradutor & Leitor de Livros Pro")
st.write("Carregue seu livro, ajuste as páginas e leia ou baixe suas traduções de forma segura.")

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

# Nova Opção: Escolher a página inicial da tradução
pagina_inicio = st.sidebar.number_input("Começar a tradução a partir da página:", min_value=1, value=1, step=1)

uploaded_file = st.file_uploader("Selecione o arquivo PDF do livro", type=["pdf"])

# Função auxiliar para gerar o PDF a partir de uma lista de páginas
def gerar_pdf_bytes(lista_paginas):
    pdf_saida = FPDF()
    pdf_saida.set_auto_page_break(auto=True, margin=15)
    for num_pag, texto_pag in lista_paginas:
        pdf_saida.add_page()
        pdf_saida.set_font("Helvetica", "B", 14)
        pdf_saida.cell(0, 10, f"Pagina {num_pag}", ln=True, align="C")
        pdf_saida.ln(5)
        pdf_saida.set_font("Helvetica", "", 11)
        texto_limpo = texto_pag.encode('latin-1', 'replace').decode('latin-1')
        pdf_saida.multi_cell(0, 6, texto_limpo)
    return pdf_saida.output()

if uploaded_file is not None:
    st.success("Livro carregado com sucesso!")
    
    if st.button("✨ Iniciar Tradução e Formatação"):
        try:
            translator = GoogleTranslator(source='auto', target=codigo_destino)
            
            paginas_traduzidas_total = []  # Guarda todas as páginas processadas nesta sessão
            bloco_atual = []               # Guarda o lote de até 50 páginas para o download parcial
            
            with pdfplumber.open(uploaded_file) as pdf:
                total_paginas = len(pdf.pages)
                
                # Validação para evitar erros caso digitem uma página maior que o livro
                if pagina_inicio > total_paginas:
                    st.error(f"Erro: O livro possui apenas {total_paginas} páginas, mas você configurou para começar da página {pagina_inicio}.")
                else:
                    st.info(f"O livro possui {total_paginas} páginas. Traduzindo da página {pagina_inicio} até {total_paginas}...")
                    
                    progresso = st.progress(0)
                    status_text = st.empty()
                    
                    # O loop agora respeita o início definido pelo usuário (ajustando o índice do Python que começa em 0)
                    for i in range(pagina_inicio - 1, total_paginas):
                        pagina = pdf.pages[i]
                        num_real_pagina = i + 1
                        
                        status_text.text(f"📖 Processando e formatando página {num_real_pagina} de {total_paginas}...")
                        
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
                            
                            # Interface de leitura organizada por abas
                            st.markdown(f"<h3 class='titulo-pagina'>Página {num_real_pagina}</h3>", unsafe_allow_html=True)
                            aba_traduzida, aba_original = st.tabs(["✨ Texto Traduzido", "📄 Texto Original"])
                            
                            with aba_traduzida:
                                st.markdown(f"<div class='caixa-leitura'>{texto_pagina_traduzida}</div>", unsafe_allow_html=True)
                            
                            with aba_original:
                                st.markdown(f"<div class='caixa-leitura' style='background-color: #f5f6fa;'>{texto_original}</div>", unsafe_allow_html=True)
                            
                            st.markdown("---")
                            
                            # Adiciona as páginas nas estruturas de dados
                            paginas_traduzidas_total.append((num_real_pagina, texto_pagina_traduzida))
                            bloco_atual.append((num_real_pagina, texto_pagina_traduzida))
                            
                            # --- LÓGICA DE DOWNLOAD A CADA 50 PÁGINAS ---
                            if len(bloco_atual) == 50:
                                p_inicial_bloco = bloco_atual[0][0]
                                p_final_bloco = bloco_atual[-1][0]
                                
                                st.markdown(f"""
                                    <div class='aviso-bloco'>
                                        <strong>💾 Bloco de segurança concluído!</strong><br>
                                        As páginas de {p_inicial_bloco} a {p_final_bloco} foram traduzidas. Faça o download abaixo para garantir o seu arquivo parcial.
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                # Gera os bytes do PDF do bloco atual de 50 páginas
                                pdf_bloco_bytes = gerar_pdf_bytes(bloco_atual)
                                
                                st.download_button(
                                    label=f"📥 Baixar Bloco Parcial (Págs {p_inicial_bloco}-{p_final_bloco})",
                                    data=io.BytesIO(pdf_bloco_bytes),
                                    file_name=f"bloco_paginas_{p_inicial_bloco}_a_{p_final_bloco}.pdf",
                                    mime="application/pdf",
                                    key=f"btn_bloco_{num_real_pagina}" # Chave única para o Streamlit não bugar no loop
                                )
                                
                                # Limpa o bloco atual para começar a contar as próximas 50
                                bloco_atual = []
                        
                        # Calcula a barra de progresso baseada nas páginas que faltam
                        total_a_traduzir = total_paginas - (pagina_inicio - 1)
                        atual_traduzido = (i - (pagina_inicio - 1)) + 1
                        progresso.progress(atual_traduzido / total_a_traduzir)
                    
                    status_text.text("✨ Processamento concluído!")
                    
                    # Se sobrou alguma página que não completou um grupo de 50 (ex: terminou na página 35 do bloco), oferece o download delas
                    if bloco_atual and len(paginas_traduzidas_total) > len(bloco_atual):
                        p_in = bloco_atual[0][0]
                        p_fi = bloco_atual[-1][0]
                        st.info(f"📥 Também está disponível o último bloco menor (Páginas {p_in} a {p_fi})")
                        st.download_button(
                            label=f"📥 Baixar Último Bloco ({p_in}-{p_fi})",
                            data=io.BytesIO(gerar_pdf_bytes(bloco_atual)),
                            file_name=f"bloco_final_{p_in}_a_{p_fi}.pdf",
                            mime="application/pdf"
                        )
                    
                    # PDF do Livro Inteiro (contando a partir de onde você começou)
                    pdf_total_bytes = gerar_pdf_bytes(paginas_traduzidas_total)
                    buffer_pdf = io.BytesIO(pdf_total_bytes)
                    
                    st.sidebar.markdown("---")
                    st.sidebar.success("Tradução Concluída!")
                    st.sidebar.download_button(
                        label=f"📥 Baixar Livro Traduzido Completo",
                        data=buffer_pdf,
                        file_name=f"livro_traduzido_desde_pag_{pagina_inicio}.pdf",
                        mime="application/pdf"
                    )
                
        except Exception as e:
            st.error(f"Ocorreu um erro durante o processo: {e}")
