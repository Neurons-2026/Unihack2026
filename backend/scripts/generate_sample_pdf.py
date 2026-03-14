"""Generate a nicely formatted PDF from the sample briefing."""
from pathlib import Path
from fpdf import FPDF

OUTPUT = Path(__file__).resolve().parent.parent / "sample_briefing.pdf"


class BriefingPDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def add_title(self, text):
        self.set_font("DejaVu", "B", 22)
        self.set_text_color(26, 26, 46)
        self.cell(0, 12, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def add_subtitle(self, text):
        self.set_font("DejaVu", "I", 10)
        self.set_text_color(120, 120, 120)
        self.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def add_divider(self):
        self.set_draw_color(200, 200, 200)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(6)

    def add_section_heading(self, text):
        self.set_font("DejaVu", "B", 14)
        self.set_text_color(26, 26, 46)
        self.multi_cell(0, 7, text)
        self.ln(2)

    def add_source_line(self, source_name, source_url):
        self.set_font("DejaVu", "I", 9)
        self.set_text_color(140, 140, 140)
        self.cell(0, 5, f"Source: {source_name} ({source_url})", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def add_label(self, text):
        self.set_font("DejaVu", "B", 11)
        self.set_text_color(26, 26, 46)
        self.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def add_body(self, text):
        self.set_font("DejaVu", "", 10)
        self.set_text_color(58, 58, 58)
        self.multi_cell(0, 5.5, text)
        self.ln(4)

    def add_link_line(self, text, url):
        self.set_font("DejaVu", "", 10)
        self.set_text_color(108, 92, 231)
        self.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT", link=url)
        self.set_text_color(58, 58, 58)
        self.ln(4)

    def add_bullet(self, text):
        self.set_font("DejaVu", "", 10)
        self.set_text_color(58, 58, 58)
        x = self.get_x()
        self.cell(6, 5.5, "-")
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def add_h2(self, text):
        self.set_font("DejaVu", "B", 16)
        self.set_text_color(26, 26, 46)
        self.cell(0, 10, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)


def build_pdf():
    pdf = BriefingPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    # Use a Unicode TTF font so em-dashes etc. render correctly
    pdf.add_font("DejaVu", "", "C:/Windows/Fonts/arial.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "C:/Windows/Fonts/arialbd.ttf", uni=True)
    pdf.add_font("DejaVu", "I", "C:/Windows/Fonts/ariali.ttf", uni=True)
    pdf.add_page()
    pdf.set_left_margin(25)
    pdf.set_right_margin(25)
    pdf.set_x(25)

    # Title
    pdf.add_title("Your AI Briefing")
    pdf.set_font("DejaVu", "", 13)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Saturday, 14 March 2026", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.add_subtitle("Based on 4 signals you saved today  |  ~10 min read")
    pdf.add_divider()

    # At a Glance
    pdf.add_h2("Today at a Glance")
    glance_items = [
        "Lightpanda releases an open-source headless browser designed specifically for AI agents, claiming 11x faster speeds than Chrome.",
        "Researchers introduce IndexCache, a technique that cuts 75% of computation in sparse attention with almost no quality loss.",
        "Wayfair deploys OpenAI models to fix millions of product tags and automate 41,000 supplier support tickets per month.",
        "Anthropic launches Claude Sonnet 4.6 with major coding, computer use, and long-context improvements plus a 1M token context window.",
    ]
    for item in glance_items:
        pdf.add_bullet(item)
    pdf.add_divider()

    # --- Card 1 ---
    pdf.add_section_heading("Lightpanda Offers Open-Source Headless Browser Built for AI Agents")
    pdf.add_source_line("GitHub", "https://github.com/lightpanda-io/browser")

    pdf.add_label("What Happened")
    pdf.add_body(
        'A startup called Lightpanda has released an open-source headless browser \u2014 a web browser that runs without a visible window, designed for automated tasks rather than human browsing. Built from scratch in a low-level programming language called Zig, Lightpanda claims to use nine times less memory and run eleven times faster than Google Chrome in headless mode. It supports JavaScript execution, works with popular automation tools like Puppeteer and Playwright, and is available for Linux, macOS, and Windows via WSL. The project is currently in beta.'
    )
    pdf.add_label("Why It Matters")
    pdf.add_body(
        "AI agents \u2014 programs that browse the web, fill out forms, and gather information on your behalf \u2014 need a browser engine to interact with modern websites. Right now, most of them rely on Chrome running invisibly in the background, which is like driving a school bus to pick up a single grocery bag. It works, but it's expensive and wasteful at scale. Lightpanda could dramatically reduce the cost and resource footprint of running thousands of AI agents simultaneously. For companies building web scraping pipelines, automated testing systems, or AI-powered research tools, a purpose-built lightweight browser means faster results and lower cloud computing bills."
    )
    pdf.add_label("What to Know")
    pdf.add_body(
        "Lightpanda is still a work in progress. It supports many core web features \u2014 JavaScript, DOM APIs (the internal structure of web pages), cookies, and form inputs \u2014 but coverage of the hundreds of existing web standards is incomplete. Some websites will still cause errors or crashes. The project respects robots.txt files (rules websites publish about what automated systems should and shouldn't access), which is a good-faith signal. It collects telemetry by default, though users can disable this with a single setting."
    )
    pdf.add_link_line("Read the full article ->", "https://github.com/lightpanda-io/browser")
    pdf.add_divider()

    # --- Card 2 ---
    pdf.add_section_heading("IndexCache Speeds Up Sparse Attention by Reusing Data Across Layers")
    pdf.add_source_line("Hugging Face Papers", "https://huggingface.co/papers/2603.12201")

    pdf.add_label("What Happened")
    pdf.add_body(
        'Researchers have published a paper introducing IndexCache, a new technique that makes a key AI efficiency method called sparse attention significantly faster. In large language models (AI systems trained on vast amounts of text), "attention" is the mechanism the model uses to figure out which words in a passage are most relevant to each other. Sparse attention speeds this up by only looking at the most important words instead of all of them, but it still requires a separate sorting step \u2014 called an indexer \u2014 at every layer of the model. IndexCache discovered that these sorting results are nearly identical across consecutive layers, so most layers can simply reuse a neighbor\'s work instead of redoing it.'
    )
    pdf.add_label("Why It Matters")
    pdf.add_body(
        "When you ask an AI to process a long document \u2014 say, a 100-page contract or an entire codebase \u2014 the model's attention mechanism becomes a major bottleneck. Every additional word makes the math exponentially harder. Sparse attention already helps, but the indexing overhead still adds up. IndexCache removes 75% of that indexing work with almost no drop in quality, resulting in responses that arrive up to 1.82 times faster during the initial processing phase. For companies running AI at scale, this kind of speedup translates directly into lower costs and snappier user experiences. The researchers confirmed these gains on a production-scale model called GLM-5, suggesting this isn't just a lab curiosity."
    )
    pdf.add_label("What to Know")
    pdf.add_body(
        "The technique was tested on DeepSeek Sparse Attention, a specific implementation used in production AI systems. IndexCache comes in two flavors: a training-free version that works immediately using a clever search algorithm, and a training-aware version that fine-tunes the remaining indexers for even better results. The paper focuses on models with 30 billion parameters and above, so these gains are most relevant for large-scale deployments rather than smaller models running on your laptop. This is a research paper, not a shipped product \u2014 but it targets real systems already in use."
    )
    pdf.add_link_line("Read the full article ->", "https://huggingface.co/papers/2603.12201")
    pdf.add_divider()

    # --- Card 3 ---
    pdf.add_section_heading("Wayfair Uses OpenAI to Fix Product Tags and Speed Up Supplier Support")
    pdf.add_source_line("OpenAI Blog", "https://openai.com/index/wayfair")

    pdf.add_label("What Happened")
    pdf.add_body(
        "Wayfair, one of the world's largest online home goods retailers, has deployed OpenAI models across two major internal systems: product catalog management and supplier support. On the catalog side, the company built a single AI system that can classify product attributes \u2014 things like color, material, and size \u2014 across its roughly 30 million items, replacing a previous approach that required building a separate custom model for each individual tag. On the support side, an AI-powered system called Wilma now reads incoming supplier tickets, identifies what's needed, fills in missing context, and routes issues to the right team. Wayfair reports correcting 2.5 million product tags and automating 41,000 support tickets per month."
    )
    pdf.add_label("Why It Matters")
    pdf.add_body(
        'This is one of the most detailed public examples of a major retailer moving AI from pilot projects into core business operations. The catalog problem is particularly instructive: Wayfair has 47,000 different attribute tags, and building a separate AI model for each one was technically possible but financially absurd. By switching to a single general-purpose model that understands context, the team expanded coverage at 70 times the previous rate. The impact isn\'t abstract \u2014 better product tags mean customers find the right items, which reduces returns and boosts search visibility. In supplier support, automating up to 70% of tickets in some workflows frees human associates to handle genuinely complex cases. The staged rollout from "co-pilot" (AI suggests, human decides) to "autopilot" (AI acts, human monitors) offers a sensible blueprint for any company worried about handing too much control to AI too quickly.'
    )
    pdf.add_label("What to Know")
    pdf.add_body(
        "Wayfair didn't simply let the AI overwrite product data without checks. When the model's confidence is high, changes go through automatically and the supplier gets notified. When confidence is lower or the tag is deemed high-risk, the system asks the supplier to confirm first. The company also has human associates physically inspecting product samples to validate AI output \u2014 a practical quality control measure. Wayfair has deployed over 1,200 ChatGPT Enterprise seats across its roughly 12,000-person workforce, signaling broad internal adoption beyond these two flagship projects."
    )
    pdf.add_link_line("Read the full article ->", "https://openai.com/index/wayfair")
    pdf.add_divider()

    # --- Card 4 ---
    pdf.add_section_heading("Anthropic Launches Claude Sonnet 4.6 With Stronger Coding and Computer Use")
    pdf.add_source_line("Anthropic Blog", "https://www.anthropic.com/news/claude-sonnet-4-6")

    pdf.add_label("What Happened")
    pdf.add_body(
        "Anthropic has released Claude Sonnet 4.6, which it calls its most capable Sonnet model yet. The new model brings significant upgrades to coding, computer use (the ability to navigate a computer screen like a human would, clicking and typing), long-context reasoning, and agent planning. It features a 1 million token context window in beta \u2014 enough to hold entire codebases or dozens of research papers in a single request. In early testing, developers preferred Sonnet 4.6 over its predecessor about 70% of the time in coding tasks, and even preferred it over the much more expensive Opus 4.5 model 59% of the time. Pricing stays the same as the previous Sonnet at $3/$15 per million tokens, and it's now the default model for free and paid users on claude.ai."
    )
    pdf.add_label("Why It Matters")
    pdf.add_body(
        'Two things stand out here. First, the computer use improvements are striking. On OSWorld, a benchmark that tests whether AI can perform real tasks on a simulated computer \u2014 navigating spreadsheets, filling out web forms, managing browser tabs \u2014 Anthropic\'s Sonnet models have shown steady gains over sixteen months. Early users report "human-level capability" on tasks like complex spreadsheet navigation. This matters because it means AI can interact with old software that was never designed to work with modern automation tools, potentially unlocking productivity gains in industries still running legacy systems. Second, the performance-per-dollar story is compelling: users are getting results comparable to Anthropic\'s most powerful (and expensive) model at a fraction of the cost, which democratizes access to frontier-level AI capabilities.'
    )
    pdf.add_label("What to Know")
    pdf.add_body(
        "Anthropic acknowledges that computer use carries risks, particularly from prompt injection attacks \u2014 where malicious instructions hidden on websites try to hijack the AI's actions. The company says Sonnet 4.6 is significantly more resistant to these attacks than its predecessor. The model supports both standard and extended thinking modes, letting developers balance speed against reasoning depth. Anthropic also announced the Claude Partner Network to help enterprises adopt Claude and The Anthropic Institute, a new initiative focused on societal challenges posed by powerful AI. For Excel users, the Claude add-in now connects to financial data providers like S&P Global and FactSet through MCP connectors."
    )
    pdf.add_link_line("Read the full article ->", "https://www.anthropic.com/news/claude-sonnet-4-6")
    pdf.add_divider()

    # Big Picture
    pdf.add_h2("Big Picture")
    pdf.add_body(
        "Today's signals paint a picture of an AI ecosystem that is rapidly maturing at every layer of the stack. At the infrastructure level, tools like Lightpanda and techniques like IndexCache are tackling the unglamorous but essential plumbing problems \u2014 making it cheaper and faster for AI systems to browse the web and process long documents. These aren't flashy product announcements, but they're the kind of foundational work that determines whether AI applications can actually scale economically. When a headless browser uses nine times less memory or an attention optimization cuts three-quarters of the computation, those savings compound across millions of users and billions of requests."
    )
    pdf.add_body(
        "At the application level, the Wayfair story and Anthropic's Sonnet 4.6 launch show what happens when that infrastructure meets real-world ambition. Wayfair offers a mature template for how large companies can move AI from experiments to production systems that touch millions of products and thousands of workers. Anthropic's advances in computer use hint at a near future where AI doesn't just generate text \u2014 it operates software the way you do, clicking through interfaces and filling out forms. The thread connecting all four signals is the same: making AI not just smarter, but more practical, more affordable, and more deeply embedded in the everyday systems people and businesses already use."
    )
    pdf.add_divider()

    # Footer
    pdf.set_font("DejaVu", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, "Generated by 10min AI Daily  |  2026-03-14T07:02:06Z", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "Sources linked above. Content summarized by AI \u2014 always verify before citing.", new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(OUTPUT))
    print(f"PDF saved to: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()
