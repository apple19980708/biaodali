import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'expression_pro.db'))


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
    ''')

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
                'title': '幸存者偏差：二战统计学家如何拯救轰炸机编队',
                'content': '1943 年，二战进入白热化阶段。美国空军对德国本土发动大规模轰炸，但轰炸机编队损失惨重。军方高层希望通过加装装甲来提高飞机生存率，但装甲过重会影响航程和载弹量，因此只能优先保护最脆弱的部位。军械师们检查了返航飞机身上的弹孔分布，发现机翼和机尾中弹最多，发动机和驾驶舱中弹最少。于是有人提议：应该在机翼和机尾加厚装甲。这个方案看似符合数据，却遭到统计学家亚伯拉罕·沃尔德的坚决反对。沃尔德敏锐地指出：我们现在能看到的弹孔数据，全部来自成功返航的飞机。那些没能返航的飞机，恰恰是因为发动机和驾驶舱中弹才坠毁的。换句话说，机翼中弹多反而说明它更耐打，真正需要保护的是数据缺失的部位。军方采纳了他的建议，把装甲集中在发动机、驾驶舱和燃油系统周围。随后几个月，轰炸机损失率显著下降，更多飞行员得以返航。这个故事后来被称为"幸存者偏差"的经典案例，它提醒我们：看不到的数据往往比看到的数据更重要。在做决策时，如果只研究成功案例而忽略失败案例，很容易得出完全相反的结论。无论是创业、投资还是个人成长，幸存者偏差都在悄悄影响我们的判断。学会追问"那些没有成功的人在哪里"，是避免这一陷阱的第一步。这一思维也解释了为什么我们看到那么多一夜暴富的故事，却很少听到无数沉默失败者的经历。',
                'difficulty': 2,
                'star_s': '1943 年，二战进入白热化阶段。美国空军对德国本土发动大规模轰炸，但轰炸机编队损失惨重。',
                'star_t': '军方希望通过加装装甲提高生存率，但装甲过重影响航程，只能优先保护最脆弱部位。',
                'star_a': '统计学家沃尔德指出返航飞机弹孔数据存在幸存者偏差，主张把装甲集中在发动机和驾驶舱等数据缺失部位。',
                'star_r': '轰炸机损失率显著下降，更多飞行员返航，这一案例也成为幸存者偏差的经典教材。',
                'keywords': '二战轰炸, 弹孔分布, 幸存者偏差, 装甲配置'
            },
            {
                'method': 'STAR',
                'title': '一个 SaaS 团队如何用"最小可行演示"拿下首单',
                'content': '2022 年春天，一家刚成立半年的 SaaS 创业团队遇到了生死关头的挑战：他们开发了一款帮助企业自动化客服工单的产品，但连续三个月没有成交，账上现金只够支撑六周。创始人李明意识到，问题不是产品不够好，而是潜在客户无法在短时间内理解产品的价值。当时团队只有四名工程师，没有专职销售，也没有任何大客户背书。李明的任务是：在两周内拿下第一个付费客户，否则公司将面临融资失败。他决定改变策略，不再给客户看功能清单和 PPT，而是直接为每家目标企业免费搭建一个"最小可行演示"——用真实数据展示如果部署他们的系统，客服响应时间能减少多少、积压工单能下降多少。为此，他让工程师开发了一个一键接入客户历史工单数据的沙盒环境，并亲自上门为五家目标客户分别演示。面对一家电商客户时，他甚至熬夜把对方过去一个月的真实投诉数据跑了进去，现场展示出平均响应时间从 6 小时压缩到 45 分钟的效果。客户当场决定先签一年合同。两周内，李明团队拿下三家付费客户，总合同金额超过八十万元，公司顺利渡过难关。这个案例后来被写入他们的销售手册：客户买的不是功能，而是可量化的业务结果。最小可行演示的核心价值，在于把抽象的承诺转化为客户能亲眼看见、亲手验证的具体场景。',
                'difficulty': 2,
                'star_s': '2022 年春天，一家 SaaS 创业团队连续三个月没有成交，账上现金只够支撑六周。',
                'star_t': '创始人李明需要在两周内拿下第一个付费客户，否则公司将融资失败。',
                'star_a': '他放弃功能清单，改为给目标客户免费搭建基于真实数据的"最小可行演示"，上门展示可量化的业务结果。',
                'star_r': '两周内拿下三家付费客户，总金额超八十万元，公司顺利渡过难关。',
                'keywords': 'SaaS创业, 最小可行演示, 真实数据, 付费客户'
            },
            {
                'method': 'PREP',
                'title': '复利思维：人生最重要的数学公式',
                'content': '我认为复利思维是普通人实现长期成长最重要的认知工具之一。复利的核心公式很简单：最终收益等于本金乘以一加收益率的年数次方。真正惊人的不是收益率本身，而是时间维度上的指数级累积。为什么复利如此重要？首先，它揭示了努力的非线性回报。在最初很长一段时间里，增长看起来微不足道，但一旦突破临界点，回报会呈现爆发式增长。其次，复利不仅适用于金钱，也适用于知识、健康和人际关系。一个人每天多读十页书、多锻炼半小时、多维护一段关系，短期几乎看不到差别，但五年十年后，这些微小的正反馈会拉开巨大的差距。巴菲特 99% 的财富是在 50 岁以后赚到的，这并非因为他 50 岁后更努力，而是因为他从年轻时就持续让资本复利滚动了半个世纪。当然，复利的前提是持续投入和避免重大回撤。一次大的健康危机、一段错误的人际关系、一笔冲动的投资，都可能让多年积累归零。因此，真正践行复利思维的人，不是追求短期爆发，而是日复一日做正确的小事，并保护好自己的本金——无论是金钱、身体还是信用。人生是一场长跑，而复利就是普通人最可靠的加速器。越早开始，越能享受时间赠予的指数红利，让平凡的努力在岁月的催化下绽放出惊人的力量。我们不必羡慕他人的一夜成名，只需专注于每天那一丁点可持续的进步。',
                'difficulty': 2,
                'prep_p': '我认为复利思维是普通人实现长期成长最重要的认知工具之一。',
                'prep_r': '复利揭示努力的非线性回报，适用于金钱、知识、健康和人际关系，时间维度上的指数累积会产生巨大差距。',
                'prep_e': '巴菲特 99% 的财富在 50 岁后获得，这源于他从年轻时就让资本复利滚动了半个世纪。',
                'prep_p2': '因此，真正践行复利思维的人应日复一日做正确的小事，并保护好本金，让人生在长跑中持续加速。',
                'keywords': '复利, 指数增长, 非线性回报, 长期主义'
            },
            {
                'method': 'PREP',
                'title': '延迟满足不是天赋，而是可以训练的能力',
                'content': '我的观点是：延迟满足能力并不是少数幸运儿与生俱来的天赋，而是每个人都可以后天训练的心理肌肉。为什么这样说？首先，心理学研究已经证明，大脑的前额叶皮层负责冲动控制和长远规划，而这一区域会随着年龄、训练和习惯养成而不断发育和强化。其次，神经科学家发现，当一个人反复经历"先忍耐、后获得更大回报"的循环时，大脑会逐步建立新的神经通路，让延迟满足变得越来越自然。棉花糖实验中被广泛引用的结论是"能等待的孩子更成功"，但后续研究真正有价值的发现在于：那些原本忍不住的孩子，在学会了一些简单策略后，等待时间可以显著延长。这意味着延迟满足是可教的。例如，把诱惑物移出视线、给自己设定明确的等待规则、把大目标拆成阶段性奖励，都能有效提升延迟满足能力。当然，这不意味着我们要压抑所有即时快乐。健康的延迟满足是有选择地放弃小诱惑，以换取更重要的长期收益。因此，与其羡慕那些天生自律的人，不如从今天开始，设计一个属于自己的"延迟满足训练计划"，从每天一次小忍耐开始，逐步重建大脑对奖励的反应模式。这种能力一旦形成，会在学习、理财和健康等多个领域持续产生复利效应，帮助我们做出更符合长远利益的决策。每一次主动选择延迟满足，都是在为未来的自己积累一笔宝贵的认知资本。',
                'difficulty': 2,
                'prep_p': '我的观点是：延迟满足能力并不是少数幸运儿与生俱来的天赋，而是每个人都可以后天训练的心理肌肉。',
                'prep_r': '前额叶皮层会随训练和习惯养成而强化，反复经历忍耐-回报循环能建立新的神经通路，棉花糖实验后续研究也证明延迟满足是可教的。',
                'prep_e': '例如，把诱惑物移出视线、设定明确等待规则、拆分阶段性奖励，都能显著提升延迟满足能力。',
                'prep_p2': '因此，与其羡慕天生自律的人，不如从今天开始设计自己的延迟满足训练计划，逐步重建大脑对奖励的反应模式。',
                'keywords': '延迟满足, 前额叶皮层, 神经可塑性, 棉花糖实验'
            },
            {
                'method': 'STAR',
                'title': '从濒临倒闭到年销千万：一个烘焙品牌的私域转型',
                'content': '2019 年冬天，杭州一家开了八年的社区烘焙店陷入危机。随着商场连锁品牌和外卖平台的冲击，门店客流连续下滑六个月，月营业额从巅峰期的三十万跌到不足八万，房东又在催缴下一季度租金。创始人周颖面临一个艰难选择：要么关店止损，要么在三个月内找到新出路。她决定把所有精力押在私域运营上。她先是把到店顾客导入微信社群，每周固定推出"会员日"和限量新品预售；然后上线小程序，让顾客可以预约自提、积分兑换和生日蛋糕定制；最后她用后台数据给高复购用户打标签，做分层推送。三个月后，社群人数突破三千，小程序订单占比超过四成，门店首次实现盈亏平衡。六个月后，会员月复购率稳定在六成以上，年营业额突破一千两百万。周颖后来总结：线下零售的命脉不是地段，而是能否把一次性客流变成可反复触达的用户资产。',
                'difficulty': 2,
                'star_s': '2019 年冬天，杭州一家开了八年的社区烘焙店陷入危机，月营业额从三十万跌到不足八万。',
                'star_t': '创始人周颖需要在三个月内找到新出路，否则只能关店止损。',
                'star_a': '她建立微信社群、上线小程序预约自提，并用数据给用户打标签做分层推送。',
                'star_r': '三个月后门店首次盈亏平衡，六个月后年营业额突破一千两百万。',
                'keywords': '私域运营, 烘焙品牌, 小程序, 复购率'
            },
            {
                'method': 'STAR',
                'title': '医生如何用三分钟讲清楚一场手术',
                'content': '在一所三甲医院的心外科，医生们发现一个长期困扰：很多患者术前签署知情同意书时神情紧张，甚至有人因为听不懂风险描述而临时拒绝手术。科主任希望改善医患沟通，让患者在充分理解的基础上做出决定。年轻医生陈帆尝试用 STAR 结构重新组织术前谈话。他先描述患者的具体病情背景，再说明手术需要解决的核心问题，接着用通俗语言讲清楚手术步骤和可能的风险点，最后总结预期效果和术后注意事项。为了更直观，他还画了一张简单流程图。三个月后，他负责的患者满意度评分从原来的七分提升到九分，术前焦虑量表得分下降近三成，知情同意书的签署效率也明显提高。医院随后把这套沟通模板推广到整个外科系统。',
                'difficulty': 2,
                'star_s': '三甲医院心外科很多患者术前紧张，甚至有人因听不懂风险描述而临时拒绝手术。',
                'star_t': '科主任希望改善医患沟通，让患者在充分理解的基础上做出决定。',
                'star_a': '医生陈帆用 STAR 结构重新组织术前谈话，并画了一张简单流程图。',
                'star_r': '患者满意度从七分提升到九分，术前焦虑下降近三成，沟通模板在全院推广。',
                'keywords': '医患沟通, 术前谈话, STAR结构, 知情同意'
            },
            {
                'method': 'STAR',
                'title': '程序员面试时如何讲清楚一个失败项目',
                'content': '2023 年春天，后端工程师张磊参加了某大厂的二面。面试官注意到他简历上有一个项目最终没有上线，便追问原因。张磊一开始有点紧张，但迅速用 STAR 结构组织回答。他说：当时团队负责的是一个实时推荐系统，目标是让首页推荐延迟降到五十毫秒以内。他负责缓存层优化，尝试引入新的内存数据库。然而测试阶段发现数据一致性无法保证，上线前三天被迫回滚。他主动复盘后发现，问题出在选型阶段没有充分评估写入并发场景。于是他改用增量更新策略，并补充了降级方案，最终在第二个迭代中把延迟降到目标值。面试官听完评价：能把失败讲出成长，比只讲成功更有说服力。两周后，张磊顺利拿到 offer。',
                'difficulty': 2,
                'star_s': '2023 年春天，后端工程师张磊面试时被追问简历上一个没有上线的失败项目。',
                'star_t': '他需要用三分钟把这个项目讲清楚，并展示自己的复盘和成长。',
                'star_a': '他用 STAR 结构描述背景、问题、行动，并重点说明如何复盘和改用增量更新策略。',
                'star_r': '面试官给出高度评价，两周后张磊顺利拿到 offer。',
                'keywords': '面试表达, 失败项目, 复盘成长, 程序员'
            },
            {
                'method': 'PREP',
                'title': '远程办公会扼杀创造力吗？我认为不会',
                'content': '我的观点是：远程办公不会扼杀创造力，反而可能激发更高质量的创新。为什么这么说？首先，创造力更多依赖深度工作、自主时间和心理安全感，而不是物理空间的 proximity。开放式办公室里的频繁打断，往往比居家办公更伤害深度思考。其次，当协作从同步转向异步，团队被迫把讨论写清楚、把决策记录下来，这种信息透明度本身就能促进更好的想法碰撞。GitLab、Automattic 和 37signals 等全球知名的全远程公司，持续推出有影响力的产品，已经证明了远程模式下的创新可能性。当然，远程办公也有挑战：缺乏非正式交流、文化稀释、新人融入变慢。但这些问题可以通过定期的线下聚会、清晰的协作规范和 mentor 制度来缓解，而不是靠强制返岗解决。因此，真正应该优化的不是"人在哪里"，而是"如何协作"。企业与其纠结是否召回员工，不如投资异步沟通工具和结果导向的管理文化。当员工拥有掌控工作节奏的自由时，他们才更有可能进入心流状态，产出真正有创造力的成果。',
                'difficulty': 2,
                'prep_p': '我的观点是：远程办公不会扼杀创造力，反而可能激发更高质量的创新。',
                'prep_r': '创造力依赖深度工作、自主时间和心理安全感，异步协作还能提升信息透明度。',
                'prep_e': 'GitLab、Automattic 和 37signals 等全远程公司持续推出有影响力的产品。',
                'prep_p2': '因此，企业应该优化异步协作和结果导向管理，而不是强制员工返岗。',
                'keywords': '远程办公, 创造力, 异步协作, 深度工作'
            },
            {
                'method': 'PREP',
                'title': '为什么我会把每天最重要的事放在早上做',
                'content': '我的观点是：每天最重要、最困难的任务应该放在早上第一件事处理。为什么这么说？首先，经过一夜休息，前额叶皮层处于最佳状态，意志力、专注力和决策质量都在一天中的高点。到了下午，连续决策会造成"决策疲劳"，让人更容易拖延、妥协或选择简单但不重要的工作。其次，心理学研究中的" ego depletion "理论虽然存在争议，但大量实证显示，人们在上午更容易进入心流状态，也更能抵抗即时诱惑。比如，许多作家、创业者和 CEO 都有固定的晨间深度工作 routine：村上春树凌晨四点开始写作，苹果 CEO 蒂姆·库克早上五点处理邮件。他们并不是天生自律，而是把宝贵的心智资源用在了刀刃上。当然，每个人的生物钟不同，夜猫子可以把"早上"调整为自己精力最好的时段。关键是，要先保护一段不被打扰的高质量时间，而不是让琐事把它切碎。因此，如果你总是被杂事牵着走，不妨试试把那只"最丑的青蛙"放在一天中最清醒的时刻吃掉。坚持一段时间，你会发现重要事项的完成率显著提高。',
                'difficulty': 2,
                'prep_p': '我的观点是：每天最重要、最困难的任务应该放在早上第一件事处理。',
                'prep_r': '早上意志力和专注力最强，下午容易出现决策疲劳，影响重要任务完成。',
                'prep_e': '村上春树凌晨四点写作，蒂姆·库克早上五点处理邮件，都是把深度工作放在精力高峰。',
                'prep_p2': '因此，把最重要的事放在一天中最清醒的时刻处理，能显著提高完成率。',
                'keywords': '时间管理, 晨间routine, 决策疲劳, 深度工作'
            },
            {
                'method': 'PREP',
                'title': '年轻人应该先攒钱还是先体验世界',
                'content': '我的观点是：年轻人在可控风险下，应该优先投资体验，而不是把所有收入都存起来。为什么这么说？首先，二十几岁时的试错成本最低。没有房贷、没有家庭负担，换城市、换行业、尝试新事物的代价相对较小。其次，丰富的体验能帮助你更快找到真正的兴趣和长期方向。很多在三十岁后才找到使命感的人，回望过去，往往发现是那些年轻时的旅行、志愿活动或短期项目给了他们关键线索。我认识的一位产品经理，大学时花三个月在东南亚做公益教育，那段经历让他意识到自己对"让复杂信息变得易懂"充满热情，后来才坚定地选择了产品这条路。当然，我并不是说可以毫无计划地挥霍。可控风险意味着：有基本储蓄兜底、不买超出能力的消费品、不因为旅行或体验背上长期债务。在这个前提下，把钱花在能拓宽视野、建立人脉和锻炼能力的体验上，是比单纯存钱更划算的投资。因此，与其在二十多岁就过紧缩生活，不如拿出一部分收入去买经历。这些经历会在未来以知识、人脉和更清晰的目标回报你。',
                'difficulty': 2,
                'prep_p': '我的观点是：年轻人在可控风险下，应该优先投资体验，而不是把所有收入都存起来。',
                'prep_r': '年轻时试错成本低，丰富体验能帮助找到真正的兴趣和长期方向。',
                'prep_e': '一位产品经理因在东南亚做公益教育的经历，坚定了选择产品方向的热情。',
                'prep_p2': '因此，在基本储蓄兜底的前提下，把钱花在拓宽视野的体验上比单纯存钱更划算。',
                'keywords': '年轻人, 攒钱, 体验, 试错成本'
            }
        ]
    for article in articles:
        if article['title'] in existing_titles:
            continue
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
    return dict(row) if row else None


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


def save_recording(user_id, cycle_id, day, module, step, transcript, ai_feedback, metrics=None):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO recordings (user_id, cycle_id, day, module, step, transcript, ai_feedback, metrics, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, cycle_id, day, module, step, transcript, ai_feedback, json.dumps(metrics, ensure_ascii=False) if metrics else None, now))
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
