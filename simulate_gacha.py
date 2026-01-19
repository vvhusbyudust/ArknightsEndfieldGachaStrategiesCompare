import random
import argparse

class GachaState:
    def __init__(self):
        self.pity_counter = 0 
        self.is_guaranteed = False 
        self.total_5_stars = 0
        self.total_up_5_stars = 0
        self.total_pulls_made = 0
        self.total_resources_spent = 0
        self.pull_history = [] 

class PoolState:
    def __init__(self):
        self.pulls_in_pool = 0
        self.up_obtained_in_pool = False
        self.bonus_30_claimed = False
        self.bonus_60_claimed = False

def simulate_pull(gacha_state, pool_state):
    current_pity = gacha_state.pity_counter
    # 0.8% base, +5% after 65 (starts 66th)
    prob = 0.008
    if current_pity >= 65: 
        prob += 0.05 * (current_pity - 64)
    if current_pity >= 79:
        prob = 1.0
        
    is_force_up_120 = False
    if pool_state.pulls_in_pool == 119 and not pool_state.up_obtained_in_pool:
        is_force_up_120 = True
        
    is_5_star = False
    if is_force_up_120:
        is_5_star = True
    else:
        if random.random() < prob:
            is_5_star = True
            
    is_up = False
    if is_5_star:
        if is_force_up_120:
            is_up = True
        else:
            if gacha_state.is_guaranteed:
                is_up = True
            else:
                is_up = random.random() < 0.5
        
        gacha_state.total_5_stars += 1
        gacha_state.pity_counter = 0 
        
        if is_up:
            gacha_state.total_up_5_stars += 1
            gacha_state.is_guaranteed = False 
            pool_state.up_obtained_in_pool = True
        else:
            gacha_state.is_guaranteed = True 
    else:
        gacha_state.pity_counter += 1
        
    pool_state.pulls_in_pool += 1
    gacha_state.total_pulls_made += 1
    return is_5_star

def simulate_free_pull(gacha_state, pool_state):
    # 免费十连逻辑 (纯赌十连):
    # 1. 概率固定 0.8% (不吃保底概率)
    # 2. 不增加保底计数
    # 3. 出货也不重置保底 (题目: "不影响任何计数")
    # 4. 出货也不消耗/享受大保底 (纯独立事件)
    
    prob = 0.008
    
    is_5_star = False
    if random.random() < prob:
        is_5_star = True
        
    if is_5_star:
        gacha_state.total_5_stars += 1
        # 注意: 不重置 pity_counter
        
        # 纯独立 50/50，不读取也不消耗 is_guaranteed
        is_up = random.random() < 0.5
            
        if is_up:
            gacha_state.total_up_5_stars += 1
            # 不更新 pool.up_obtained_in_pool (因为不影响计数? 或者影响?)
            # 题目说 "119抽若都没有获取up... 120抽必定出"
            # 如果免费十连出了 UP，是否还要 120 强娶？
            # "不影响任何计数" -> 可能意味着这单纯是送的，不以此判断 120 规则？
            # 但既然已经拿到了 UP，通常逻辑是该池子目标达成。
            # 为了严谨，假设它单纯是“额外掉落”，不影响池子状态。
            pass
        else:
            pass
    else:
        pass # 不加计数
        
    # 免费抽不增加 total_pulls_made (为了计算 avg_pulls 纯粹性? 还是增加?)
    # 但如果是“额外赠送”，通常不计入“使用了的资源折算的抽数”。
    # 之前的代码加了。这里保持加，方便看总样本量。
    gacha_state.total_pulls_made += 1
    return is_5_star

def run_strategy(strategy_type, total_resources, n_sims=1):
    results = []
    
    for _ in range(n_sims):
        state = GachaState()
        resources_left = total_resources
        next_pool_coupon = 0 
        pool_index = 0 
        
        # 状态机变量 for optimized strategies
        is_padding_phase = False 
        
        if strategy_type == "all_in_up":
            is_padding_phase = False 
        elif "pad" in strategy_type and "then" in strategy_type:
             is_padding_phase = True
        elif "opt" in strategy_type:
            is_padding_phase = True 
        
        while resources_left > 0:
            pool = PoolState()
            pool_strategy = "unknown"
            
            if strategy_type == "all_in_up":
                pool_strategy = "target_up"
            elif strategy_type == "fixed_60":
                pool_strategy = "fixed_60"
            elif strategy_type == "pad30_then_up":
                if pool_index % 2 == 0: pool_strategy = "pad_30_fixed"
                else: pool_strategy = "target_up"
            elif strategy_type == "pad60_then_up":
                if pool_index % 2 == 0: pool_strategy = "pad_60_fixed"
                else: pool_strategy = "target_up"
            elif strategy_type == "pad30_opt":
                if is_padding_phase: pool_strategy = "pad_30_opt"
                else: pool_strategy = "target_up"
            elif strategy_type == "pad60_opt":
                if is_padding_phase: pool_strategy = "pad_60_opt"
                else: pool_strategy = "target_up"

            padding_success = False 

            while True:
                should_stop_pool = False
                
                if pool_strategy == "pad_30_fixed":
                    if pool.pulls_in_pool >= 30: should_stop_pool = True
                
                elif pool_strategy == "pad_60_fixed":
                    if pool.pulls_in_pool >= 60: should_stop_pool = True
                    
                # 新增 fixed_60 逻辑: 雷打不动 60 抽
                elif pool_strategy == "fixed_60":
                    if pool.pulls_in_pool >= 60: should_stop_pool = True
                        
                elif pool_strategy == "target_up":
                    if pool.up_obtained_in_pool or pool.pulls_in_pool >= 120:
                        should_stop_pool = True
                
                elif pool_strategy == "pad_30_opt":
                    if pool.up_obtained_in_pool and pool.pulls_in_pool < 30:
                        should_stop_pool = True
                        padding_success = False
                    if pool.pulls_in_pool >= 30:
                        should_stop_pool = True
                        padding_success = True
                
                elif pool_strategy == "pad_60_opt":
                    if pool.up_obtained_in_pool and pool.pulls_in_pool < 60:
                        should_stop_pool = True
                        padding_success = False
                    if pool.pulls_in_pool >= 60:
                        should_stop_pool = True
                        padding_success = True

                if should_stop_pool or (resources_left <= 0 and next_pool_coupon <= 0):
                    break
                    
                if pool.pulls_in_pool == 30 and not pool.bonus_30_claimed:
                    pool.bonus_30_claimed = True
                    for _ in range(10): simulate_free_pull(state, pool)
                    continue 

                if pool.pulls_in_pool == 60 and not pool.bonus_60_claimed:
                    pool.bonus_60_claimed = True
                    pass 

                if next_pool_coupon > 0: next_pool_coupon -= 1
                else:
                    if resources_left > 0: 
                        resources_left -= 1
                        state.total_resources_spent += 1 
                    else: break 
                
                simulate_pull(state, pool)
            
            if strategy_type in ["pad30_opt", "pad60_opt"]:
                if is_padding_phase:
                    if padding_success: is_padding_phase = False 
                    else: is_padding_phase = True 
                else:
                    is_padding_phase = True
            
            if pool.bonus_60_claimed: next_pool_coupon = 10
            else: next_pool_coupon = 0
            
            pool_index += 1
            
        results.append(state)
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--resources", type=int, default=10000)
    parser.add_argument("--sims", type=int, default=1000)
    args = parser.parse_args()
    
    strats = ["pad30_then_up", "pad30_opt", "pad60_then_up", "pad60_opt", "fixed_60", "all_in_up"]
    print(f"正在模拟 {args.sims} 次运行，每次 {args.resources} 资源...")
    print("策略说明:")
    print("  pad30/60_then_up: 固定交替 (1垫1抽)")
    print("  pad30/60_opt:     优化交替 (垫出货则重垫)")
    print("  fixed_60:         雷打不动 (每个池子固定60抽)")
    print("  all_in_up:        死磕 UP (每个池子都抽满)")
    print("-" * 40)
    
    for s in strats:
        results = run_strategy(s, args.resources, args.sims)
        
        total_5s = sum(r.total_5_stars for r in results)
        total_up = sum(r.total_up_5_stars for r in results)
        total_spent = sum(r.total_resources_spent for r in results)
        total_pulls = sum(r.total_pulls_made for r in results)
        
        avg_cost_per_5 = total_spent / total_5s if total_5s > 0 else float('inf')
        avg_cost_per_up = total_spent / total_up if total_up > 0 else float('inf')
        avg_pulls = total_pulls / args.sims
        
        print(f"策略: {s}")
        print(f"  平均消耗资源/五星:    {avg_cost_per_5:.2f} 券")
        print(f"  平均消耗资源/UP五星:  {avg_cost_per_up:.2f} 券")
        print(f"  平均总抽数:           {avg_pulls:.2f} 抽")
        print("-" * 40)
