import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

def create_time_matrix(season):
    # 創建24小時 x 7天的矩陣
    matrix = np.zeros((24, 7))
    
    # 設定值對應：0=off-peak, 1=mid-peak, 2=peak, 3=Sat. mid-peak
    if season == 'summer':
        # 週一到週五
        for day in range(5):
            matrix[0:9, day] = 0  # 00:00-08:59 off-peak
            matrix[9:16, day] = 1  # 09:00-15:59 mid-peak
            matrix[16:22, day] = 2  # 16:00-21:59 peak
            matrix[22:24, day] = 1  # 22:00-23:59 mid-peak
        
        # 週六
        matrix[0:9, 5] = 0  # 00:00-08:59 off-peak
        matrix[9:24, 5] = 3  # 09:00-23:59 Sat. mid-peak
        
        # 週日
        matrix[:, 6] = 0  # 全天 off-peak
        
    else:  # nonsummer
        # 週一到週五
        matrix[0:6, :5] = 0  # 00:00-05:59 off-peak
        matrix[6:11, :5] = 1  # 06:00-10:59 mid-peak
        matrix[11:14, :5] = 0  # 11:00-13:59 off-peak
        matrix[14:24, :5] = 1  # 14:00-23:59 mid-peak
        
        # 週六
        matrix[0:6, 5] = 0  # 00:00-05:59 off-peak
        matrix[6:11, 5] = 3  # 06:00-10:59 Sat. mid-peak
        matrix[11:14, 5] = 0  # 11:00-13:59 off-peak
        matrix[14:24, 5] = 3  # 14:00-23:59 Sat. mid-peak
        
        # 週日
        matrix[:, 6] = 0  # 全天 off-peak
        
    return matrix

def plot_time_of_use(season):
    matrix = create_time_matrix(season)
    
    plt.figure(figsize=(12, 8))
    
    # 設定不同季節的顏色方案
    if season == 'summer':
        colors = ['#E6F3FF', '#FFB266', '#FF3333']  # 淺藍、橙色、紅色
        vmax = 2
    else:
        colors = ['#E6F3FF', '#FFB266']  # 淺藍、橙色
        vmax = 1
    
    # 創建熱力圖，添加格線
    ax = sns.heatmap(matrix, 
                     cmap=colors,
                     cbar_kws={'ticks': range(vmax + 1)},
                     yticklabels=range(24),
                     xticklabels=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                     linewidths=0.5,  # 添加格線
                     linecolor='gray',  # 格線顏色
                     vmin=0,
                     vmax=vmax)
    
    plt.title(f'Time-of-Use Periods - {season.capitalize()} Season')
    plt.ylabel('Hour of Day')
    plt.xlabel('Day of Week')
    
    # 修改colorbar標籤
    colorbar = ax.collections[0].colorbar
    if season == 'summer':
        colorbar.set_ticks([0.33, 1, 1.67])
        colorbar.set_ticklabels(['Off-Peak', 'Mid-Peak', 'Peak'])
    else:
        colorbar.set_ticks([0.25, 0.75])
        colorbar.set_ticklabels(['Off-Peak', 'Mid-Peak'])
    
    plt.tight_layout()
    plt.savefig(f'{season}_tou.png', dpi=300, bbox_inches='tight')
    plt.close()

# 生成兩個季節的圖表
plot_time_of_use('summer')
plot_time_of_use('nonsummer') 