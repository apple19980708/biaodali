import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'expression_pro.db'))


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_columns_exist(cursor, table, columns):
    """Add missing columns to an existing table (idempotent migration helper)."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    if not cursor.fetchone():
        return
    cursor.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cursor.fetchall()}
    for name, definition in columns:
        if name not in existing:
            cursor.execute(f'ALTER TABLE {table} ADD COLUMN {name} {definition}')


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            current_method TEXT,
            cycle_day INTEGER DEFAULT 0,
            cycle_total_days INTEGER DEFAULT 4,
            state TEXT DEFAULT 'select_method'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cycles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            method TEXT NOT NULL,
            total_days INTEGER DEFAULT 4,
            current_day INTEGER DEFAULT 1,
            completed_articles_count INTEGER DEFAULT 0,
            used_article_ids TEXT DEFAULT '[]',
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
    ''')

    # Migrate existing databases
    _ensure_columns_exist(cursor, 'cycles', [
        ('completed_articles_count', 'INTEGER DEFAULT 0'),
        ('used_article_ids', 'TEXT DEFAULT \'[]\'')
    ])

    _ensure_columns_exist(cursor, 'recordings', [
        ('llm_used', 'INTEGER DEFAULT 0'),
        ('llm_provider', 'TEXT')
    ])

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            cycle_id INTEGER NOT NULL,
            day INTEGER NOT NULL,
            article_id INTEGER,
            method_learned INTEGER DEFAULT 0,
            drag_completed INTEGER DEFAULT 0,
            qa_completed INTEGER DEFAULT 0,
            retell_completed INTEGER DEFAULT 0,
            free_completed INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, cycle_id, day)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drag_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            cycle_id INTEGER NOT NULL,
            day INTEGER NOT NULL,
            mappings TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            cycle_id INTEGER NOT NULL,
            day INTEGER NOT NULL,
            module TEXT NOT NULL,
            step TEXT NOT NULL,
            transcript TEXT,
            ai_feedback TEXT,
            metrics TEXT,
            created_at TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            checkin_date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, checkin_date)
        )
    ''')

    conn.commit()
    conn.close()


def seed_data():
    """Seed articles and methods if not present."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            method TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            difficulty INTEGER DEFAULT 1,
            star_s TEXT,
            star_t TEXT,
            star_a TEXT,
            star_r TEXT,
            prep_p TEXT,
            prep_r TEXT,
            prep_e TEXT,
            prep_p2 TEXT,
            keywords TEXT
        )
    ''')

    cursor.execute('SELECT title FROM articles')
    existing_titles = {row[0] for row in cursor.fetchall()}

    articles = [
            {
                'method': 'STAR',
                'title': '沃尔德与轰炸机：一个被误读的统计学故事',
                'content': '二战期间，盟军对德国本土发动大规模战略轰炸，但轰炸机损失率高得惊人。为了提高生存率，军方决定对返航飞机进行弹孔统计，把有限的装甲加到中弹最密集的部位。军械师们汇总了大量数据后发现：机翼和机尾弹孔最多，发动机和驾驶舱弹孔最少。于是，一个看似顺理成章的方案被提了出来——加固机翼和机尾。但统计学家亚伯拉罕·沃尔德坚决反对。他指出，军方犯下了一个根本性的样本错误：他们只看到成功返航的飞机，而被击落坠毁的飞机根本无法纳入统计。那些消失的飞机之所以没能回来，很可能正是因为发动机或驾驶舱中弹。换句话说，机翼上弹孔多，恰恰说明机翼经得起打击；真正致命、需要装甲保护的，是数据中似乎"最安全"的部位。沃尔德的建议最初遭到不少质疑，因为反直觉，但军方最终采纳了他的方案，把装甲集中在发动机、驾驶舱和燃油系统周围。随后的作战数据显示，轰炸机损失率显著下降。这个故事后来被称为"幸存者偏差"的经典注脚，它提醒我们：最危险的不是已知的风险，而是那些因为样本缺失而被系统性忽略的风险。在创业、投资、医疗甚至日常决策中，我们往往热衷于研究成功案例，却对沉默的失败群体视而不见。真正清醒的思考者，会主动追问：我没有看到什么？',
                'difficulty': 2,
                'star_s': '二战期间，盟军轰炸机损失惨重，军方希望通过统计返航飞机弹孔来优化装甲配置。',
                'star_t': '军方需要判断到底应该加固机翼、机尾，还是发动机和驾驶舱这些看似中弹少的部位。',
                'star_a': '军方最终采纳了沃尔德的建议，把装甲集中在发动机、驾驶舱和燃油系统周围。',
                'star_r': '轰炸机损失率显著下降，"幸存者偏差"成为统计学与决策思维中的经典案例。',
                'keywords': '幸存者偏差, 二战轰炸, 样本选择, 反直觉决策'
            },
            {
                'method': 'STAR',
                'title': '阿波罗 13 号：当任务失败成为最伟大的成功',
                'content': '1970 年 4 月，阿波罗 13 号在飞往月球的途中，服务舱的一个氧气罐突然爆炸。飞船失去了大部分电力、氧气和推进能力，三名宇航员的生命危在旦夕。登月已经不可能，地面控制中心和宇航员必须想尽一切办法，把三人安全带回地球。此时，飞船上的指令舱电力几乎耗尽，舱内二氧化碳浓度迅速上升，可供呼吸的空气越来越少。NASA 地面团队必须利用飞船上有限的物资，在极短时间内设计出一套应急方案。工程师们临时用胶带、塑料袋和手册上的零件，拼凑出一个二氧化碳过滤装置；导航团队精确计算了数次轨道修正，确保飞船以正确的角度再入大气层；同时，宇航员被指令进入登月舱，把它当作一艘临时救生艇。在接下来的四天里，数千名工程师、飞行员和科学家几乎不眠不休地协作。最终，阿波罗 13 号指令舱在南太平洋安全溅落，三名宇航员全部生还。这次飞行虽然未能登月，却被视为航天史上最伟大的救援行动之一。它证明了一个深刻的道理：真正的能力不仅在于按计划完成目标，更在于当计划彻底崩塌时，依然能够保持冷静、整合资源并找到出路。',
                'difficulty': 2,
                'star_s': '1970 年 4 月，阿波罗 13 号服务舱氧气罐爆炸，三名宇航员面临生命危险。',
                'star_t': '登月已经不可能，地面控制中心和宇航员必须想尽一切办法把三人安全带回地球。',
                'star_a': '地面团队临时制作二氧化碳过滤装置，精确计算轨道修正，并把登月舱当作救生艇。',
                'star_r': '三名宇航员全部安全返回，这次飞行成为航天史上最伟大的救援行动之一。',
                'keywords': '阿波罗13号, 危机管理, 即兴创新, 团队协作'
            },
            {
                'method': 'STAR',
                'title': '微信的诞生：一个被内部质疑的项目如何突围',
                'content': '2010 年，腾讯已经拥有手机 QQ，但张小龙和他的团队意识到，移动互联网时代需要一种更轻、更快、更贴近手机体验的沟通方式。他们开始立项微信，却在公司内部引发了大量质疑：手机 QQ 已经占据市场，用户为什么还需要另一款类似产品？即使做出来，会不会反而侵蚀 QQ 的用户？张小龙坚持认为，QQ 的架构和功能是为 PC 时代设计的，而手机原生应用需要完全不同的产品哲学。在巨头林立、用户习惯尚未形成的窗口期，他需要打造一款能够重新定义移动社交的产品。团队选择了一条极简路径，从免费即时消息和语音对讲切入，刻意保持界面干净，避免功能堆砌。随后，他们逐步推出朋友圈、公众号、微信支付和小程序，每一次扩展都围绕"连接"这个核心逻辑展开。微信上线后增长迅速，短短一年多时间用户破亿，并在随后十年成长为月活超过 13 亿的超级应用。它不仅改变了人们的沟通方式，也重塑了内容创作、商业交易和公共讨论的整个生态。微信的成功证明：真正的创新往往不是复制已有的成功，而是敢于在组织内部质疑主流叙事，为尚未被满足的需求开辟新的产品形态。',
                'difficulty': 2,
                'star_s': '2010 年，腾讯内部已有手机 QQ，张小龙团队提出做微信时遭到大量质疑。',
                'star_t': '在巨头林立、用户习惯尚未形成的窗口期，张小龙需要打造一款能够重新定义移动社交的产品。',
                'star_a': '张小龙坚持极简设计，从免费消息和语音对讲切入，逐步扩展朋友圈、公众号和小程序。',
                'star_r': '微信成长为月活超 13 亿的超级应用，重新定义了中文互联网的社交基础设施。',
                'keywords': '微信, 产品创新, 极简设计, 移动社交'
            },
            {
                'method': 'STAR',
                'title': '张文宏的疫情沟通：专业表达如何穿越恐慌',
                'content': '2020 年初，新冠疫情突然暴发，公众面对的是大量未知、矛盾的信息和迅速蔓延的恐慌。在这种情况下，医学专家不仅要提供科学建议，还要在信息碎片化和情绪化的环境中建立公众信任。张文宏作为一名感染科医生，承担了向公众解释疫情的角色。在不确定性极高的情况下，他要把复杂的医学信息翻译成普通人能理解和执行的建议，同时避免制造新的恐慌。张文宏选择了一种直接、坦诚且有温度的表达方式。他用通俗语言解释病毒传播链，明确告诉人们"少出门、戴口罩、勤洗手"为什么有效；在一线压力最大的时候，他说"党员先上"，用具体行动承担责任；面对未知，他不回避，而是清楚说明科学判断的依据和局限。他的表达里没有高高在上的说教，也没有模棱两可的安抚。几个月后，张文宏成为公众最信任的医学专家之一，他的沟通方式也被视为危机传播的典型案例。这个故事说明：在公共危机中，最有效的表达不是最华丽的，而是最诚实、最具体、最能让人采取行动的。',
                'difficulty': 2,
                'star_s': '2020 年初新冠疫情暴发，公众信息混乱、恐慌蔓延，医学专家需要在不确定中建立信任。',
                'star_t': '在不确定性极高的情况下，张文宏要把复杂的医学信息翻译成普通人可执行的建议，同时避免制造恐慌。',
                'star_a': '他用通俗语言解释传播链，直言承担责任，不回避未知，持续发布基于证据的判断。',
                'star_r': '他成为公众最信任的医学专家之一，其沟通方式成为危机传播的典型案例。',
                'keywords': '公共卫生, 危机沟通, 专业表达, 信任建立'
            },
            {
                'method': 'STAR',
                'title': '瑞幸重生：从造假丑闻到商业模式重构',
                'content': '2020 年，瑞幸咖啡自曝财务造假 22 亿元人民币，公司股价一夜暴跌 80%，面临退市、诉讼和信任崩塌的多重危机。这家曾以激进补贴和快速扩张著称的咖啡品牌，几乎在一夜之间成为中概股丑闻的代名词。新管理层上任后，必须在废墟上重建一个可持续的商业模式，同时向资本市场、供应商和消费者证明公司还有继续经营的价值。他们没有选择继续掩盖或逃避，而是公开承认错误，更换核心团队，启动与监管机构和投资者的和解，并迅速调整战略。具体行动上，瑞幸关闭了长期亏损的门店，优化了供应链，减少了补贴依赖，同时大力发展自提和外卖数字化运营，推出爆款产品如生椰拿铁。两年后，瑞幸实现了扭亏为盈，门店数量反超星巴克中国，成为中国咖啡市场的重要力量。它的反转并非因为奇迹，而是因为敢于直面问题、砍掉虚假增长、回归商业本质。瑞幸的案例提醒我们：危机本身并不可怕，可怕的是用错误的方式延续错误。',
                'difficulty': 2,
                'star_s': '2020 年，瑞幸咖啡自曝财务造假，股价暴跌，面临退市、诉讼和信任崩塌。',
                'star_t': '新管理层必须在废墟上重建可持续商业模式，并向市场证明公司仍有继续经营的价值。',
                'star_a': '他们承认错误、更换团队、关闭亏损门店、优化供应链，并发展数字化和爆款产品。',
                'star_r': '两年后瑞幸扭亏为盈，门店数反超星巴克中国，成为危机反转的罕见案例。',
                'keywords': '瑞幸咖啡, 财务造假, 危机反转, 商业模式重构'
            },
            {
                'method': 'PREP',
                'title': '我们高估了天赋，低估了系统',
                'content': '我的观点是：大多数人把成功过多归因于天赋，却忽视了支撑结果的系统与环境。为什么这样说？首先，心理学和绩效管理的研究反复证明，刻意练习、反馈密度、资源可及性和制度设计对长期表现的影响，远远超过先天能力。同样的个体，在不同的规则和文化下，会呈现出完全不同的行为模式和成就上限。其次，天赋是一个很难被准确定义的概念。我们常常在事后把成功者的某些特质称为"天赋"，却忽略了他们成长过程中无数次的试错、支持和机遇。例如，芬兰教育体系从不强调竞争和天赋筛选，却持续在国际测评中表现优异；许多被视为"天才"的运动员、音乐家和科学家，背后往往是家庭支持、早期投入和优质导师的叠加。这并不是说努力不重要，而是说我们容易把复杂的成功叙事简化为一两个天才个人的故事，从而忽视了那些可以被复制和改进的系统性因素。因此，与其羡慕别人的天赋，不如为自己设计一套可持续的成长系统：清晰的目标、稳定的反馈、适度的压力和充足的恢复。当一个人处在好的系统中时，平凡的能力也能被放大；反之，再高的天赋也可能被糟糕的环境消磨殆尽。',
                'difficulty': 2,
                'prep_p': '我的观点是：大多数人把成功过多归因于天赋，却忽视了支撑结果的系统与环境。',
                'prep_r': '刻意练习、反馈密度、资源可及性和制度设计对长期表现的影响远超先天能力。',
                'prep_e': '芬兰教育体系不强调天赋筛选却持续优异，许多"天才"背后是家庭、导师和早期投入的系统叠加。',
                'prep_p2': '因此，与其羡慕天赋，不如为自己设计一套可持续的成长系统，让能力在好环境中被放大。',
                'keywords': '天赋, 成长系统, 刻意练习, 环境设计'
            },
            {
                'method': 'PREP',
                'title': '批判性思维正在被信息茧房侵蚀',
                'content': '我的观点是：真正稀缺的不是信息，而是穿越信息茧房的批判性思维能力。为什么这么说？首先，算法推荐不断强化我们已有的观点，让我们误以为看到的就是世界的全貌。其次，碎片化、情绪化的内容比理性论证更容易获得传播，因为愤怒和认同总是比审慎和思考更能激发点击和转发。结果是，许多人每天消费大量信息，却没有意识到这些信息是被筛选和编排过的。例如，同一社会事件在不同平台可能呈现出截然相反的事实版本和道德判断，而用户往往只停留在自己熟悉的平台上，从未接触过对立视角。更危险的是，人们会逐渐失去区分事实、观点和情绪的能力，把"我感觉"等同于"事实就是"。批判性思维不是简单地反对一切，而是在面对信息时先问三个问题：这个信息的来源是什么？它遗漏了哪些反例？作者的立场和利益是什么？因此，我们需要主动寻找异质信息源，阅读与自己立场不同的论证，并在表达时为自己的判断提供证据。只有如此，我们才能在信息丰裕的时代避免变得更加狭隘和偏激。',
                'difficulty': 2,
                'prep_p': '我的观点是：真正稀缺的不是信息，而是穿越信息茧房的批判性思维能力。',
                'prep_r': '算法推荐强化既有观点，情绪化内容比理性论证更易传播，导致人们误把片面当全貌。',
                'prep_e': '同一社会事件在不同平台呈现截然相反的事实版本，许多人却从未接触过对立视角。',
                'prep_p2': '因此，我们应主动寻找异质信息源，区分事实、观点和情绪，避免在信息时代变得更狭隘。',
                'keywords': '信息茧房, 批判性思维, 算法推荐, 媒介素养'
            },
            {
                'method': 'PREP',
                'title': '真正的高效，不是做更多而是做更少',
                'content': '我的观点是：高效的本质不是提高做事速度，而是敢于对不重要的事说不。为什么这么说？首先，人的认知带宽有限，每增加一个并行任务，都会降低决策质量和执行深度。表面上的忙碌往往掩盖了真正重要的事情被无限拖延的事实。其次，"多任务处理"在很大程度上是一种幻觉，大脑在任务切换中消耗大量能量，反而会降低整体产出。例如，乔布斯 1997 年回归苹果后，做的第一件事不是推出更多产品，而是把产品线从数十条砍到四条。这个看似收缩的决策，反而让团队聚焦资源，推出 iMac、iPod 和 iPhone，带领公司起死回生。许多顶尖创作者和企业家都有类似的"不做清单"：他们明确列出自己不参与、不回应、不投资的事情，以此保护深度工作的时间。当然，做减法并不容易，因为拒绝意味着承担机会成本，也意味着要面对他人的期待。但如果不做减法，我们就会被琐事淹没，永远没有时间处理那些真正重要的事情。因此，提高效率的第一步不是管理时间，而是识别并剔除低价值任务，把稀缺资源集中在关键少数上。',
                'difficulty': 2,
                'prep_p': '我的观点是：高效的本质不是提高做事速度，而是敢于对不重要的事说不。',
                'prep_r': '认知带宽有限，多任务切换降低决策质量，表面忙碌掩盖关键事项被拖延。',
                'prep_e': '乔布斯回归苹果后把产品线从数十条砍到四条，反而让公司起死回生并推出 iMac、iPod 和 iPhone。',
                'prep_p2': '因此，提高效率的第一步是剔除低价值任务，把稀缺资源集中在关键少数上。',
                'keywords': '高效, 做减法, 深度工作, 关键少数'
            },
            {
                'method': 'PREP',
                'title': '教育的终极目标不是就业而是自主',
                'content': '我的观点是：教育最重要的目标不是培养合格的雇员，而是培养能够自主判断、持续学习的独立个体。为什么这样说？首先，职业结构正在快速变化，今天热门的技能可能十年后就被淘汰。如果教育只传授固定知识，学生离开学校后将难以应对未知挑战。其次，现代社会的问题越来越复杂，从公共卫生到人工智能伦理，从气候危机到社会公平，都需要公民具备独立思考、辨别信息和参与公共讨论的能力，而不是被动接受标准答案。例如，芬兰和新加坡的教育体系更重视问题解决、合作学习和元认知能力，而不是单纯的知识记忆和考试排名。这些国家的学生不仅在学业测评中表现优异，在创新能力和心理韧性方面也更具优势。当然，就业是教育的重要功能之一，但把它当作唯一目标会窄化教育的价值。当一个人被训练成只会执行指令的员工，他可能会在短期内获得稳定收入，却很难在职业生涯中实现真正的成长和意义感。因此，衡量教育质量的标准不应只是升学率和就业率，更应该是学生离开学校后是否还拥有学习的动力、批判的能力和选择人生的自主性。',
                'difficulty': 2,
                'prep_p': '我的观点是：教育最重要的目标不是培养合格的雇员，而是培养能够自主判断、持续学习的独立个体。',
                'prep_r': '职业结构快速变化，社会问题日益复杂，固定知识和标准答案无法应对未来挑战。',
                'prep_e': '芬兰和新加坡重视问题解决、合作学习和元认知能力，学生学业、创新和韧性表现均更优。',
                'prep_p2': '因此，教育质量应看学生离校后是否仍有学习动力、批判能力和选择人生的自主性。',
                'keywords': '教育目标, 自主学习, 批判能力, 终身学习'
            },
            {
                'method': 'PREP',
                'title': '善意的无效帮助，比不帮助更伤人',
                'content': '我的观点是：未经请求的、低质量的善意帮助，有时比不帮助更具破坏性。为什么这样说？首先，过度帮助会剥夺他人的自主感和成长机会，让受助者陷入依赖，甚至怀疑自己的能力。其次，帮助者容易陷入"我为你好"的道德优越感，忽视受助者的真实需求和情境。这种帮助往往满足的是帮助者自己的情感需求，而不是对方的实际需要。例如，在国际援助领域，大量免费物资捐赠曾压垮非洲本地产业，因为当地生产者无法与免费商品竞争，反而失去了生计。在家庭教育中，父母包办一切的孩子常常缺乏抗挫折能力和问题解决能力，因为他们从未被允许独立面对困难。当然，我并不是说应该冷漠旁观。真正有效的帮助需要先倾听、先理解，尊重对方的主体性，在对方明确需要支持时才提供恰当的资源，而不是替代对方完成任务。因此，最好的帮助不是给予最多，而是给予刚好足够让对方能够站起来继续前行的支持。帮助的最高境界，是让对方不再需要你的帮助。',
                'difficulty': 2,
                'prep_p': '我的观点是：未经请求的、低质量的善意帮助，有时比不帮助更具破坏性。',
                'prep_r': '过度帮助剥夺自主感和成长机会，帮助者也容易陷入道德优越感而忽视真实需求。',
                'prep_e': '国际援助中的免费物资曾压垮本地产业，包办一切的家庭教育让孩子缺乏抗挫折能力。',
                'prep_p2': '因此，真正有效的帮助应先倾听需求、尊重主体性，让对方能够独立继续前行。',
                'keywords': '帮助, 自主性, 依赖性, 有效援助'
            }
        ]
    for article in articles:
        if article['title'] in existing_titles:
            # Update existing article so fixes to star/prep fields and content propagate
            cursor.execute('''
                UPDATE articles SET
                    method = ?, content = ?, difficulty = ?,
                    star_s = ?, star_t = ?, star_a = ?, star_r = ?,
                    prep_p = ?, prep_r = ?, prep_e = ?, prep_p2 = ?, keywords = ?
                WHERE title = ?
            ''', (
                article['method'], article['content'], article['difficulty'],
                article.get('star_s', ''), article.get('star_t', ''), article.get('star_a', ''), article.get('star_r', ''),
                article.get('prep_p', ''), article.get('prep_r', ''), article.get('prep_e', ''), article.get('prep_p2', ''),
                article.get('keywords', ''),
                article['title']
            ))
        else:
            cursor.execute('''
                INSERT INTO articles (method, title, content, difficulty, star_s, star_t, star_a, star_r, prep_p, prep_r, prep_e, prep_p2, keywords)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article['method'], article['title'], article['content'], article['difficulty'],
                article.get('star_s', ''), article.get('star_t', ''), article.get('star_a', ''), article.get('star_r', ''),
                article.get('prep_p', ''), article.get('prep_r', ''), article.get('prep_e', ''), article.get('prep_p2', ''),
                article.get('keywords', '')
            ))

    conn.commit()
    conn.close()


def get_or_create_user(user_id='U10086'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    if not user:
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO users (user_id, created_at, state)
            VALUES (?, ?, ?)
        ''', (user_id, now, 'home'))
        conn.commit()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
    conn.close()
    return dict(user)


def update_user_state(user_id, updates):
    conn = get_connection()
    cursor = conn.cursor()
    fields = ', '.join([f'{k} = ?' for k in updates.keys()])
    values = list(updates.values()) + [user_id]
    cursor.execute(f'UPDATE users SET {fields} WHERE user_id = ?', values)
    conn.commit()
    conn.close()


def reset_user_progress(user_id):
    """Clear all progress for a user while keeping articles and methods."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM checkins WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM recordings WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM drag_analysis WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM daily_progress WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM cycles WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


def get_active_cycle(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM cycles WHERE user_id = ? AND status = ? ORDER BY id DESC LIMIT 1', (user_id, 'active'))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    cycle = dict(row)
    # Keep the counter in sync with actual daily_progress so display never drifts
    cycle['completed_articles_count'] = sync_completed_articles_count(cycle['id'])
    # Unified article number for all "第 X 篇" displays (1-based, current learning article)
    cycle['current_article_number'] = cycle['current_day']
    return cycle


def create_cycle(user_id, method, total_days=4):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO cycles (user_id, method, total_days, current_day, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, method, total_days, 1, now))
    conn.commit()
    cycle_id = cursor.lastrowid
    conn.close()
    return cycle_id


def complete_cycle(cycle_id):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('UPDATE cycles SET status = ?, completed_at = ? WHERE id = ?', ('completed', now, cycle_id))
    conn.commit()
    conn.close()


def get_or_create_daily_progress(user_id, cycle_id, day):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM daily_progress WHERE user_id = ? AND cycle_id = ? AND day = ?', (user_id, cycle_id, day))
    row = cursor.fetchone()
    if not row:
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO daily_progress (user_id, cycle_id, day, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, cycle_id, day, now))
        conn.commit()
        cursor.execute('SELECT * FROM daily_progress WHERE user_id = ? AND cycle_id = ? AND day = ?', (user_id, cycle_id, day))
        row = cursor.fetchone()
    conn.close()
    return dict(row)


def update_daily_progress(user_id, cycle_id, day, updates):
    conn = get_connection()
    cursor = conn.cursor()
    fields = ', '.join([f'{k} = ?' for k in updates.keys()])
    values = list(updates.values()) + [user_id, cycle_id, day]
    cursor.execute(f'UPDATE daily_progress SET {fields} WHERE user_id = ? AND cycle_id = ? AND day = ?', values)
    conn.commit()
    conn.close()


def reset_daily_progress(user_id, cycle_id, day):
    """Reset a single day's progress so the user can practice again."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE daily_progress
        SET article_id = NULL, method_learned = 0, drag_completed = 0,
            qa_completed = 0, retell_completed = 0, free_completed = 0, completed = 0
        WHERE user_id = ? AND cycle_id = ? AND day = ?
    ''', (user_id, cycle_id, day))
    cursor.execute('DELETE FROM recordings WHERE user_id = ? AND cycle_id = ? AND day = ?', (user_id, cycle_id, day))
    cursor.execute('DELETE FROM drag_analysis WHERE user_id = ? AND cycle_id = ? AND day = ?', (user_id, cycle_id, day))
    conn.commit()
    conn.close()


def get_cycle_used_article_ids(cycle_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT used_article_ids FROM cycles WHERE id = ?', (cycle_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        try:
            return json.loads(row[0])
        except Exception:
            return []
    return []


def add_cycle_used_article_id(cycle_id, article_id):
    if not article_id:
        return
    used = get_cycle_used_article_ids(cycle_id)
    if article_id not in used:
        used.append(article_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE cycles SET used_article_ids = ? WHERE id = ?', (json.dumps(used), cycle_id))
    conn.commit()
    conn.close()


def increment_completed_articles_count(cycle_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE cycles SET completed_articles_count = completed_articles_count + 1 WHERE id = ?', (cycle_id,))
    conn.commit()
    conn.close()


def get_completed_articles_count(cycle_id):
    """Count distinct days marked as completed in the current cycle."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(DISTINCT day) FROM daily_progress
        WHERE cycle_id = ? AND completed = 1
    ''', (cycle_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def sync_completed_articles_count(cycle_id):
    """Sync cycles.completed_articles_count with actual completed days."""
    actual = get_completed_articles_count(cycle_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE cycles SET completed_articles_count = ? WHERE id = ?', (actual, cycle_id))
    conn.commit()
    conn.close()
    return actual


def get_article_for_method(method, exclude_ids=None):
    conn = get_connection()
    cursor = conn.cursor()
    if exclude_ids:
        placeholders = ','.join(['?'] * len(exclude_ids))
        cursor.execute(f'SELECT * FROM articles WHERE method = ? AND id NOT IN ({placeholders}) ORDER BY RANDOM() LIMIT 1', (method, *exclude_ids))
    else:
        cursor.execute('SELECT * FROM articles WHERE method = ? ORDER BY RANDOM() LIMIT 1', (method,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_article_by_id(article_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM articles WHERE id = ?', (article_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_drag_analysis(user_id, cycle_id, day, mappings):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO drag_analysis (user_id, cycle_id, day, mappings, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, cycle_id, day, json.dumps(mappings, ensure_ascii=False), now))
    conn.commit()
    conn.close()


def save_recording(user_id, cycle_id, day, module, step, transcript, ai_feedback, metrics=None, llm_used=0, llm_provider=None):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO recordings (user_id, cycle_id, day, module, step, transcript, ai_feedback, metrics, llm_used, llm_provider, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, cycle_id, day, module, step, transcript, ai_feedback,
          json.dumps(metrics, ensure_ascii=False) if metrics else None,
          1 if llm_used else 0, llm_provider, now))
    conn.commit()
    conn.close()


def checkin_today(user_id='U10086'):
    """Record today's check-in. Returns True if new, False if already exists."""
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().date().isoformat()
    now = datetime.now().isoformat()
    try:
        cursor.execute('''
            INSERT INTO checkins (user_id, checkin_date, created_at)
            VALUES (?, ?, ?)
        ''', (user_id, today, now))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def get_checkin_dates(user_id='U10086', start_date=None, end_date=None):
    """Get set of check-in dates in range."""
    conn = get_connection()
    cursor = conn.cursor()
    if start_date and end_date:
        cursor.execute('''
            SELECT checkin_date FROM checkins
            WHERE user_id = ? AND checkin_date >= ? AND checkin_date <= ?
        ''', (user_id, start_date, end_date))
    else:
        cursor.execute('SELECT checkin_date FROM checkins WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return {row['checkin_date'] for row in rows}


def get_streak(user_id='U10086'):
    """Calculate current consecutive check-in streak."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT checkin_date FROM checkins WHERE user_id = ? ORDER BY checkin_date DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return 0

    dates = sorted([row['checkin_date'] for row in rows], reverse=True)
    from datetime import date, timedelta
    streak = 0
    check_date = date.today()

    # If no check-in today, start from yesterday
    if dates[0] != check_date.isoformat():
        check_date = date.today() - timedelta(days=1)

    for d in dates:
        if d == check_date.isoformat():
            streak += 1
            check_date -= timedelta(days=1)
        elif d > check_date.isoformat():
            continue
        else:
            break

    return streak


if __name__ == '__main__':
    init_db()
    seed_data()
    print('Database initialized and seeded.')
