/*
    Copyright (c) 2005-2022 Intel Corporation

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
*/

#ifndef _ITTNOTIFY_TYPES_H_
#define _ITTNOTIFY_TYPES_H_

typedef enum ___itt_group_id
{
    __itt_group_none      		= 0,
    __itt_group_legacy    		= 1<<0,
    __itt_group_control   		= 1<<1,
    __itt_group_thread    		= 1<<2,
    __itt_group_mark      		= 1<<3,
    __itt_group_sync      		= 1<<4,
    __itt_group_fsync     		= 1<<5,
    __itt_group_jit       		= 1<<6,
    __itt_group_model     		= 1<<7,
    __itt_group_splitter_min 	= 1<<7,
    __itt_group_counter   		= 1<<8,
    __itt_group_frame     		= 1<<9,
    __itt_group_stitch    		= 1<<10,
    __itt_group_heap      		= 1<<11,
    __itt_group_splitter_max 	= 1<<12,
    __itt_group_structure 		= 1<<12,
    __itt_group_suppress 		= 1<<13,
    __itt_group_arrays    		= 1<<14,
    __itt_group_module    		= 1<<15,
    __itt_group_all       		= -1
} __itt_group_id;

#pragma pack(push, 8)

typedef struct ___itt_group_list
{
    __itt_group_id id;
    const char*    name;
} __itt_group_list;

#pragma pack(pop)

#define ITT_GROUP_LIST(varname) \
    static __itt_group_list varname[] = {       \
        { __itt_group_all,       "all"       }, \
        { __itt_group_control,   "control"   }, \
        { __itt_group_thread,    "thread"    }, \
        { __itt_group_mark,      "mark"      }, \
        { __itt_group_sync,      "sync"      }, \
        { __itt_group_fsync,     "fsync"     }, \
        { __itt_group_jit,       "jit"       }, \
        { __itt_group_model,     "model"     }, \
        { __itt_group_counter,   "counter"   }, \
        { __itt_group_frame,     "frame"     }, \
        { __itt_group_stitch,    "stitch"    }, \
        { __itt_group_heap,      "heap"      }, \
        { __itt_group_structure, "structure" }, \
        { __itt_group_suppress,  "suppress"  }, \
        { __itt_group_arrays,    "arrays"    }, \
		{ __itt_group_module,    "module"    }, \
        { __itt_group_none,      NULL        }  \
    }

#endif /* _ITTNOTIFY_TYPES_H_ */
