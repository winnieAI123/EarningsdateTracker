import type { CategorizedCompanies } from './types';

export const CATEGORIZED_COMPANIES: CategorizedCompanies = {
  '科技': [
    { name: 'Oracle Corporation', ticker: 'ORCL', domain: 'oracle.com', chineseName: '甲骨文' },
    { name: 'Taiwan Semiconductor Manufacturing Company', ticker: 'TSM', domain: 'tsmc.com', chineseName: '台积电' },
    { name: 'Advanced Micro Devices, Inc.', ticker: 'AMD', domain: 'amd.com', chineseName: 'AMD' },
    { name: 'Palantir Technologies Inc.', ticker: 'PLTR', domain: 'palantir.com', chineseName: 'Palantir' },
    { name: 'Meta Platforms, Inc.', ticker: 'META', domain: 'meta.com', chineseName: 'Meta' },
    { name: 'International Business Machines Corporation', ticker: 'IBM', domain: 'ibm.com', chineseName: 'IBM' },
    { name: 'Intel Corporation', ticker: 'INTC', domain: 'intel.com', chineseName: '英特尔' },
    { name: 'NVIDIA Corporation', ticker: 'NVDA', domain: 'nvidia.com', chineseName: '英伟达' },
    { name: 'Microsoft Corporation', ticker: 'MSFT', domain: 'microsoft.com', chineseName: '微软' },
    { name: 'Amazon.com, Inc.', ticker: 'AMZN', domain: 'amazon.com', chineseName: '亚马逊' },
    { name: 'Alphabet Inc.', ticker: 'GOOGL', domain: 'abc.xyz', chineseName: '谷歌' },
    { name: 'Tesla, Inc.', ticker: 'TSLA', domain: 'tesla.com', chineseName: '特斯拉' },
    { name: 'Apple Inc.', ticker: 'AAPL', domain: 'apple.com', chineseName: '苹果' },
  ],
  '消费': [
    { name: 'Nayuki Holdings Ltd', ticker: '2150.HK', domain: 'nayuki.com', chineseName: '奈雪的茶' },
    { name: 'Luckin Coffee Inc.', ticker: 'LKNCY', domain: 'luckincoffee.com', chineseName: '瑞幸咖啡' },
    { name: 'Starbucks Corporation', ticker: 'SBUX', domain: 'starbucks.com', chineseName: '星巴克' },
    { name: 'LVMH Moët Hennessy Louis Vuitton SE', ticker: 'MC.PA', domain: 'lvmh.com', chineseName: 'LVMH' },
    { name: 'Hermès International S.A.', ticker: 'RMS.PA', domain: 'hermes.com', chineseName: '爱马仕' },
    { name: 'Mixue Bingcheng Co., Ltd.', ticker: '2418.HK', domain: 'mxbc.com', chineseName: '蜜雪冰城' },
    { name: 'Laopu Gold Co., Ltd.', ticker: '6181.HK', domain: 'laopuhuangjin.com', chineseName: '老铺黄金' },
    { name: 'Pop Mart International Group Limited', ticker: '9992.HK', domain: 'popmart.com', chineseName: '泡泡玛特' },
    { name: 'QuantaSing Group Limited', ticker: 'QSG', domain: 'quantasing.com', chineseName: '量子之歌' },
  ],
  '教育': [
    { name: 'New Oriental Education & Technology Group Inc.', ticker: 'EDU', domain: 'neworiental.org', chineseName: '新东方' },
    { name: 'TAL Education Group', ticker: 'TAL', domain: '100tal.com', chineseName: '好未来' },
    { name: 'Gaotu Techedu Inc.', ticker: 'GOTU', domain: 'gaotu.cn', chineseName: '高途' },
    { name: 'iFLYTEK CO.,LTD.', ticker: '002230.SZ', domain: 'iflytek.com', chineseName: '科大讯飞' },
    { name: 'Duolingo, Inc.', ticker: 'DUOL', domain: 'duolingo.com', chineseName: '多邻国' },
    { name: 'Youdao, Inc.', ticker: 'DAO', domain: 'youdao.com', chineseName: '有道' },
  ],
};
